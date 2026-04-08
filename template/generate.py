"""
Task: [TASK NAME]
Description: [BRIEF DESCRIPTION]

Author: [YOUR NAME]
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
from pathlib import Path
from src.task import Task


class TaskName(Task):
    """
    [DESCRIBE WHAT THIS TASK SIMULATES AND WHAT THE MODEL MUST DO]
    """

    def generate(self):
        """
        Generate input data and ground truth.
        
        Must populate:
            self.input_data/     ← files sent to model
            self.ground_truth/   ← JSON files used by grader
            self.visualisations/ ← reference plots (not graded)
        """
        
        # Load difficulty parameters
        params = self.config['difficulties'][self.difficulty]
        
        # Set random seed if specified
        seed = self.seed if self.seed is not None else params.get('seed')
        if seed is not None:
            np.random.seed(seed)
        
        # =====================================================
        # TODO: Generate data, ground truth and populate
        # =====================================================
        # Here comes the main code used to generate the task

        raise NotImplementedError("Implement data generation")
        pass

