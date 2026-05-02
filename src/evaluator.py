import json
import re
from datetime import datetime
from pathlib import Path
import docker
import shutil
import tempfile
import time

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from src.task import Task, TaskResults, MetarubricResult
from src.utils import get_git_hash
from src.tools import TOOLS, _load_sandbox_libraries

import litellm
litellm.request_timeout = 300

class Evaluator:

    # ─────────────────────────────────────────
    # Public interface
    # ─────────────────────────────────────────
    def run(self, task: Task, model: str, judge: str,
            agentic: bool = False,
            max_turns: int  = 10) -> TaskResults:
        """Run full evaluation pipeline for one task/model/seed."""

        # Step 1 — send task to model
        if agentic:
            model_output = self._send_to_model_agentic(task, model, max_turns)
        else:
            model_output = self._send_to_model(task, model)

        # Step 2 — judge output against pre-generated rubrics
        mr_results = self._judge(task, model_output, judge)

        # Step 3 — build and return TaskResults
        return TaskResults(
            task_name          = task.folder.name,
            seed               = task.seed,
            difficulty         = task.difficulty,
            model              = model,
            judge              = judge,
            git_commit         = get_git_hash(),
            timestamp          = datetime.now().isoformat(),
            metarubric_results = mr_results
        )

    # ─────────────────────────────────────────
    # Repeating attempts in case model API is unavailable
    # ─────────────────────────────────────────
    def _litellm_completion_with_retry(self, **kwargs):
        for attempt in range(3):
            try:
                return litellm.completion(**kwargs)
            except (litellm.ServiceUnavailableError,
                    litellm.RateLimitError) as e:
                if attempt == 2:
                    print(e)
                    print(f"✗ API unavailable after 3 attempts:")
                    raise
                wait = 30 * (attempt + 1)
                print(f"ERROR: {e}")
                print(f"⚠  API unavailable — retrying in {wait}s ({attempt+1}/3)")
                time.sleep(wait)

    # ─────────────────────────────────────────
    # Load judge prompt
    # ─────────────────────────────────────────
    def _load_judge_prompt(self, model_output: str, criteria: str) -> str:
        """Load judge prompt"""
        template = (Path(__file__).parent / 'judge_prompt.md').read_text()
        return template.format(model_output = model_output,
                               criteria = criteria)
    
    # ─────────────────────────────────────────
    # Load agentic prompt
    # ─────────────────────────────────────────
    def load_agentic_prompt(self, max_turns: int, vision: bool = True) -> str:
        """Load agentic prompt addition and fill in available libraries."""
        template = (Path(__file__).parent / 'agentic_prompt.md').read_text()
        view_image_note = ", and `view_image` to inspect image files" if vision else ""
        view_image_tool = (
            "- **view_image** — render an image file into your context so you can inspect it visually\n"
            if vision else ""
        )
        return template.format(
            libraries       = _load_sandbox_libraries(),
            max_turns       = max_turns,
            view_image_tool = view_image_tool,
            view_image_note = view_image_note,
        )

    # ─────────────────────────────────────────
    # Send to model
    # ─────────────────────────────────────────
    def _send_to_model(self, task: Task, model: str) -> str:
        """Build message from task prompt + input files, call model, return response."""
        messages = [{
            'role':    'user',
            'content': [
                {'type': 'text', 'text': task.get_prompt()},
                *task.get_input_files(model)
            ]
        }]

        try:
            response = self._litellm_completion_with_retry(
                model    = model,
                messages = messages,
                temperature = 0.0,
            )
            model_output = response.choices[0].message.content
    
            print(f"\n{'=' * 50}")
            print(f"MODEL OUTPUT ({model}):")
            print(f"{'=' * 50}")
            print(model_output)
            
            return model_output

        except litellm.AuthenticationError:
            print(f"✗ Authentication failed for '{model}' — check your API key")
            raise

        except Exception as e:
            print(f"✗ Model call failed: {e}")
            raise

    # ─────────────────────────────────────────
    # Send to model - multiple turns for agent
    # ─────────────────────────────────────────
    def _send_to_model_agentic(self, task: Task, model: str,
                            max_turns: int) -> str:
        """
        Agentic evaluation — model can write and execute Python scripts.
        Images are included in the first message and remain accessible
        throughout the conversation via the full history.
        A persistent workspace is shared across all turns so the agent
        can save and load intermediate files between tool calls.
        """
        # Create persistent workspace for this session
        session_dir = Path(tempfile.mkdtemp())

        try:
            # Copy input files once into session workspace
            shutil.copytree(task.input_dir, session_dir, dirs_exist_ok=True)

            # Providers that support multimodal content in tool result messages.
            # litellm.supports_vision() only checks the model, not whether the
            # provider accepts image blocks in tool results — Groq e.g. does not.
            _VISION_TOOL_PROVIDERS = {'anthropic', 'openai', 'azure', 'gemini', 'vertex_ai', 'bedrock', 'ollama'}
            try:
                _, provider, _, _ = litellm.get_llm_provider(model)
            except Exception:
                provider = ''
            vision   = provider in _VISION_TOOL_PROVIDERS and litellm.supports_vision(model=model)
            tools    = TOOLS if vision else [t for t in TOOLS if t['function']['name'] != 'view_image']

            # Include input files in the first message
            messages = [{
                'role':    'user',
                'content': [
                    {'type': 'text',
                     'text': task.get_prompt() + self.load_agentic_prompt(max_turns, vision)},
                            *task.get_input_files(model, embed_data=False)
                ]
            }]

            for turn in range(max_turns):
                response = self._litellm_completion_with_retry(
                    model       = model,
                    messages    = messages,
                    tools       = tools,
                    temperature = 0.0
                )

                if not response.choices:
                    raise RuntimeError(
                        f"Model {model} returned an empty response (no choices). "
                    )
                message = response.choices[0].message

                # No tool calls — model finished analysis, ask for summary
                if not message.tool_calls:
                    messages.append(message.model_dump())
                    messages.append({
                        'role':    'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': (
                                    'Analysis complete. Now state your final results '
                                    'explicitly following the output format specified '
                                    'in the task instructions. Do not use any tools — '
                                    'only summarise your findings in plain text.'
                                )
                            }
                        ]
                    })

                    summary = self._litellm_completion_with_retry(
                        model       = model,
                        messages    = messages,
                        temperature = 0.0
                    )

                    final_answer = summary.choices[0].message.content or ''

                    print(f"\n{'-' * 50}")
                    print("FINAL ANSWER:")
                    print('-' * 50)
                    print(final_answer)

                    return final_answer

                # Append assistant turn to history
                messages.append(message.model_dump())

                for tool_call in message.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)

                    print(f"\n{'-' * 50}")
                    print(f"TOOL CALL {name!r} (turn {turn + 1}):")
                    print(f"\n{'-' * 50}")

                    if name == 'execute_python':
                        output = self._execute_python(args['code'], session_dir)
                        print(args['code'])
                        print(f"OUTPUT:")
                        print(output)

                        if len(output) > 5000:
                            output = output[:5000] + "\n...(truncated)"

                        messages.append({
                            'role':         'tool',
                            'tool_call_id': tool_call.id,
                            'name':         'execute_python',
                            'content':      output
                        })

                    elif name == 'run_command':
                        command = args['command']
                        print(f"command: {command}")
                        content = self._run_command(command, session_dir)
                        print(content)
                        messages.append({
                            'role':         'tool',
                            'tool_call_id': tool_call.id,
                            'name':         'run_command',
                            'content':      content
                        })

                    elif name == 'write_file':
                        path, content = args['path'], args['content']
                        print(f"path: {path}")
                        result = self._write_file(path, content, session_dir)
                        print(result)
                        messages.append({
                            'role':         'tool',
                            'tool_call_id': tool_call.id,
                            'name':         'write_file',
                            'content':      result
                        })

                    elif name == 'read_file':
                        path = args['path']
                        print(f"path: {path}")
                        content = self._read_file(path, session_dir)
                        print(content)
                        messages.append({
                            'role':         'tool',
                            'tool_call_id': tool_call.id,
                            'name':         'read_file',
                            'content':      content
                        })

                    elif name == 'view_image':
                        path = args['path']
                        print(f"path: {path}")
                        content = self._view_image(path, session_dir)
                        messages.append({
                            'role':         'tool',
                            'tool_call_id': tool_call.id,
                            'name':         'view_image',
                            'content':      content
                        })

                    else:
                        print(f"WARNING: unknown tool '{name}' — returning error to model")
                        messages.append({
                            'role':         'tool',
                            'tool_call_id': tool_call.id,
                            'name':         name,
                            'content':      f"Error: unknown tool '{name}'."
                        })


            # Max turns reached — ask for summary of what was found
            messages.append({
                'role':    'user',
                'content': [
                    {
                        'type': 'text',
                        'text': (
                            'Maximum tool calls reached. State your final results '
                            'explicitly following the output format specified in the '
                            'task instructions based on what you have found so far.'
                        )
                    }
                ]
            })

            summary = self._litellm_completion_with_retry(
                model       = model,
                messages    = messages,
                temperature = 0.0
            )

            final_answer = summary.choices[0].message.content or "No summary produced."

            print(f"\n{'-' * 50}")
            print("FINAL ANSWER (max turns reached):")
            print('-' * 50)
            print(final_answer)

            return final_answer

        finally:
            # Clean up session workspace — always runs even if exception occurs
            shutil.rmtree(session_dir, ignore_errors=True)



    # ─────────────────────────────────────────
    # Judge
    # ─────────────────────────────────────────
    def _judge(self, task: Task,
               model_output: str,
               judge: str) -> list[MetarubricResult]:
        """Load pre-generated rubrics and judge model output against them."""

        with open(task.ground_truth_dir / 'rubrics.json') as f:
            rubrics_data = json.load(f)

        results = []
        for mr_data in rubrics_data['metarubrics']:
            rubrics = [r['criterion'] for r in mr_data['rubrics']]
            passed  = self._judge_metarubric(rubrics, model_output, judge)

            results.append(MetarubricResult(
                metarubric_name = mr_data['name'],
                total           = len(rubrics),
                passed          = passed,
                weight          = mr_data['weight']
            ))

        return results

    # ─────────────────────────────────────────
    # Judge metarubrics either as batch or single
    # ─────────────────────────────────────────
    def _judge_metarubric(self, rubrics: list[str],
                           model_output: str,
                           judge: str) -> int:    
        """
        Judge all criteria in one metarubric.
        Uses batch call for API judges, single calls for local models.
        """
        if judge.startswith('ollama/'):
            # Local models — one call per rubric, more reliable
            passed = 0
            for rubric in rubrics:
                if self._judge_single(rubric, model_output, judge):
                    passed += 1
            return passed
        else:
            # API models — batch all rubrics in one call
            return self._judge_batch(rubrics, model_output, judge)

    # ─────────────────────────────────────────
    # Judge single rubric item
    # ─────────────────────────────────────────
    def _judge_single(self, rubric: str,
                       model_output: str,
                       judge: str) -> bool:
        
        """One rubric, one YES/NO question"""
        prompt = self._load_judge_prompt(model_output = model_output,
                                        criteria = rubric)

        try:
            response = self._litellm_completion_with_retry(
                model       = judge,
                messages    = [{'role': 'user', 'content': prompt}],
                temperature = 0.0
            )
            answer = response.choices[0].message.content.strip().upper()
            return answer.startswith('YES')

        except Exception as e:
            print(f"⚠  Judge call failed: {e} — counting as not passed")
            return False
        
    # ─────────────────────────────────────────
    # Batch rubrics in one metarubric
    # ─────────────────────────────────────────
    def _judge_batch(self, rubrics: list[str],
                  model_output: str,
                  judge: str) -> int:
        """
        Send all rubrics in one call — for capable API models.
        Returns number of criteria passed.
        """
        numbered = '\n'.join(
            f"{i+1}. {r}" for i, r in enumerate(rubrics)
        )
        
        """Batch of rubrics, multiple YES/NO questions"""
        prompt = self._load_judge_prompt(model_output = model_output,
                                        criteria = numbered)

        try:
            response = self._litellm_completion_with_retry(
                model       = judge,
                messages    = [{'role': 'user', 'content': prompt}],
                temperature = 0.0
            )
            raw = response.choices[0].message.content.strip()
            
            # Strip markdown if present
            raw = re.sub(r'```json\s*', '', raw)
            raw = re.sub(r'```\s*',     '', raw)
            raw = raw.strip()
            
            verdicts = json.loads(raw)
            
            if len(verdicts) != len(rubrics):
                print(f"⚠  Judge returned {len(verdicts)} verdicts for {len(rubrics)} rubrics")
                return 0
            
            return sum(1 for v in verdicts if v)
        
        except json.JSONDecodeError:
            print(f"⚠  Judge parse failed — raw response: {raw[:200]}")
            return 0
        
        except Exception as e:
            print(f"⚠  Judge call failed: {e} — counting as not passed")
            return 0

    # ─────────────────────────────────────────
    # Run shell command in Docker sandbox
    # ─────────────────────────────────────────
    _ALLOWED_COMMANDS = {
        'grep', 'sed', 'awk', 'find', 'head', 'tail',
        'cat', 'wc', 'sort', 'uniq', 'cut', 'ls', 'file',
        'mkdir', 'touch', 'cp', 'cd',
    }

    def _run_command(self, command: str, session_dir: Path, max_chars: int = 5_000) -> str:
        # Validate every command segment (split on ||, &&, |, ;)
        for segment in re.split(r'\|\||&&|[|;]', command):
            tokens = segment.strip().split()
            if not tokens:
                continue
            if tokens[0] not in self._ALLOWED_COMMANDS:
                allowed = ', '.join(sorted(self._ALLOWED_COMMANDS))
                return f"Error: '{tokens[0]}' is not allowed. Allowed commands: {allowed}."

        # Check Docker daemon is running before attempting anything
        try:
            client = docker.from_env()
            client.ping()
        except docker.errors.DockerException:
            raise RuntimeError(
                "⚠  Docker daemon is not running. "
                "Start Docker Desktop and try again."
            )

        # Use persistent session_dir
        tmpdir  = session_dir
        mode    = 'rw'      # read-write — agent can save files
        cleanup = False     # session_dir managed by caller

        try:
            output = client.containers.run(
                image         = 'benchmark-sandbox',
                command       = ['sh', '-c', command],
                working_dir   = '/home/agent/workspace',
                user          = 'agent',
                network_mode  = 'none',
                mem_limit     = '512m',
                memswap_limit = '512m',
                cpu_quota     = 50000,
                pids_limit    = 64,
                volumes       = {
                    str(tmpdir): {
                        'bind': '/home/agent/workspace',
                        'mode': mode
                    }
                },
                tmpfs         = {'/tmp': ''},
                detach        = False,
                stdout        = True,
                stderr        = True,
                remove        = True,
            )

            result = output.decode() if output else "(no output)"

        except docker.errors.ContainerError as e:
            result = e.stderr.decode() if e.stderr else str(e)

        except Exception as e:
            result = f"Execution error: {e}"

        finally:
            if cleanup:
                shutil.rmtree(tmpdir, ignore_errors=True)

        if len(result) > max_chars:
            result = result[:max_chars] + f"\n...(truncated at {max_chars} chars)"
        return result

    # ─────────────────────────────────────────
    # Write text file on agents request
    # ─────────────────────────────────────────
    def _write_file(self, path: str, content: str, session_dir: Path) -> str:
        file_path = session_dir / path
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            return f"Written {len(content)} chars to '{path}'."
        except Exception as e:
            return f"Error writing '{path}': {e}"

    # ─────────────────────────────────────────
    # Read text/csv file on agents request
    # ─────────────────────────────────────────
    def _read_file(self, path: str, session_dir: Path, max_chars: int = 10_000) -> str:
        file_path = session_dir / path
        if not file_path.exists():
            return f"Error: '{path}' not found in workspace."
        try:
            content = file_path.read_text()
        except Exception as e:
            return f"Error reading '{path}': {e}"
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n...(truncated at {max_chars} chars)"
        return content

    # View image on agents request
    # ─────────────────────────────────────────
    def _view_image(self, path: str, session_dir: Path):
        import base64, mimetypes
        image_path = session_dir / path
        if not image_path.exists():
            return f"Error: '{path}' not found in workspace."
        mime_type, _ = mimetypes.guess_type(str(image_path))
        if mime_type not in ('image/png', 'image/jpeg', 'image/gif', 'image/webp'):
            return f"Error: '{path}' is not a supported image type (png/jpeg/gif/webp)."
        data = base64.standard_b64encode(image_path.read_bytes()).decode()
        return [
            {'type': 'text',      'text': f"Image '{path}':"},
            {'type': 'image_url', 'image_url': {'url': f'data:{mime_type};base64,{data}'}}
        ]

    # ─────────────────────────────────────────
    # Execute Python in Docker container sandbox
    # ─────────────────────────────────────────
    def _execute_python(self, code: str, session_dir: Path) -> str:
        """
        Execute model-generated Python code in an isolated Docker container.
        If session_dir is provided, it is mounted as read-write workspace
        allowing the agent to persist files between turns.
        Otherwise a fresh read-only workspace is created per call.
        """
        # Check Docker daemon is running before attempting anything
        try:
            client = docker.from_env()
            client.ping()
        except docker.errors.DockerException:
            raise RuntimeError(
                "⚠  Docker daemon is not running. "
                "Start Docker Desktop and try again."
            )

        # Use persistent session_dir
        tmpdir  = session_dir
        mode    = 'rw'      # read-write — agent can save files
        cleanup = False     # session_dir managed by caller

        try:
            # Write script into workspace
            (tmpdir / 'script.py').write_text(code)

            output = client.containers.run(
                image         = 'benchmark-sandbox',
                command       = 'python /home/agent/workspace/script.py',
                working_dir   = '/home/agent/workspace',
                user          = 'agent',
                network_mode  = 'none',
                mem_limit     = '512m',
                memswap_limit = '512m',
                cpu_quota     = 50000,
                volumes       = {
                    str(tmpdir): {
                        'bind': '/home/agent/workspace',
                        'mode': mode
                    }
                },
                tmpfs         = {'/tmp': ''},
                detach        = False,
                stdout        = True,
                stderr        = True,
                remove        = True,
            )

            return output.decode() if output else "(no output)"

        except docker.errors.ContainerError as e:
            return e.stderr.decode() if e.stderr else str(e)

        except Exception as e:
            return f"Execution error: {e}"

        finally:
            if cleanup:
                shutil.rmtree(tmpdir, ignore_errors=True)