# MIT License
#
# Copyright (C) IBM Corporation 2018
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
This module implements the Knockoff Nets attack `KnockoffNets`.

| Paper link: https://arxiv.org/abs/1812.02766
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging

import numpy as np

from art.config import ART_NUMPY_DTYPE
from art.attacks.attack import ExtractionAttack
from art.classifiers.classifier import Classifier
from art.utils import to_categorical


logger = logging.getLogger(__name__)


class KnockoffNets(ExtractionAttack):
    """
    Implementation of the Knockoff Nets attack from Orekondy et al. (2018).

    | Paper link: https://arxiv.org/abs/1812.02766
    """
    attack_params = ExtractionAttack.attack_params + ['batch_size_fit', 'batch_size_query', 'nb_epochs',
                                                      'nb_stolen', 'sampling_strategy', 'reward']

    def __init__(self, classifier, batch_size_fit=1, batch_size_query=1, nb_epochs=10, nb_stolen=1,
                 sampling_strategy='random', reward='all'):
        """
        Create a copycat cnn attack instance.

        :param classifier: A victim classifier.
        :type classifier: :class:`.Classifier`
        :param batch_size_fit: Size of batches for fitting the thieved classifier.
        :type batch_size_fit: `int`
        :param batch_size_query: Size of batches for querying the victim classifier.
        :type batch_size_query: `int`
        :param nb_epochs: Number of epochs to use for training.
        :type nb_epochs: `int`
        :param nb_stolen: Number of queries submitted to the victim classifier to steal it.
        :type nb_stolen: `int`
        :param sampling_strategy: Sampling strategy, either `random` or `adaptive`.
        :type sampling_strategy: `string`
        :param reward: Reward type, in ['cert', 'div', 'loss', 'all'].
        :type reward: `string`
        """
        super(KnockoffNets, self).__init__(classifier=classifier)

        params = {'batch_size_fit': batch_size_fit,
                  'batch_size_query': batch_size_query,
                  'nb_epochs': nb_epochs,
                  'nb_stolen': nb_stolen,
                  'sampling_strategy': sampling_strategy,
                  'reward': reward}
        self.set_params(**params)

    def extract(self, x, y=None, **kwargs):
        """
        Extract a thieved classifier.

        :param x: An array with the source input to the victim classifier.
        :type x: `np.ndarray`
        :param y: Target values (class labels) one-hot-encoded of shape (nb_samples, nb_classes) or indices of shape
                  (nb_samples,).
        :type y: `np.ndarray` or `None`
        :param thieved_classifier: A thieved classifier to be stolen.
        :type thieved_classifier: :class:`.Classifier`
        :return: The stolen classifier.
        :rtype: :class:`.Classifier`
        """
        # Check prerequisite for random strategy
        if self.sampling_strategy == 'random' and y is not None:
            logger.warning("This attack with random sampling strategy does not use the provided label y.")

        # Check prerequisite for adaptive strategy
        if self.sampling_strategy == 'adaptive' and y is None:
            raise ValueError("This attack with adaptive sampling strategy needs label y.")

        # Check the size of the source input vs nb_stolen
        if x.shape[0] < self.nb_stolen:
            logger.warning("The size of the source input is smaller than the expected number of queries submitted "
                           "to the victim classifier.")

        # Check if there is a thieved classifier provided for training
        thieved_classifier = kwargs.get('thieved_classifier')
        if thieved_classifier is None or not isinstance(thieved_classifier, Classifier):
            raise ValueError('A thieved classifier is needed.')


        return thieved_classifier

    def set_params(self, **kwargs):
        """
        Take in a dictionary of parameters and applies attack-specific checks before saving them as attributes.

        :param batch_size_fit: Size of batches for fitting the thieved classifier.
        :type batch_size_fit: `int`
        :param batch_size_query: Size of batches for querying the victim classifier.
        :type batch_size_query: `int`
        :param nb_epochs: Number of epochs to use for training.
        :type nb_epochs: `int`
        :param nb_stolen: Number of queries submitted to the victim classifier to steal it.
        :type nb_stolen: `int`
        :param sampling_strategy: Sampling strategy, either `random` or `adaptive`.
        :type sampling_strategy: `string`
        :param reward: Reward type, in ['cert', 'div', 'loss', 'all'].
        :type reward: `string`
        """
        # Save attack-specific parameters
        super(KnockoffNets, self).set_params(**kwargs)

        if not isinstance(self.batch_size_fit, (int, np.int)) or self.batch_size_fit <= 0:
            raise ValueError("The size of batches for fitting the thieved classifier must be a positive integer.")

        if not isinstance(self.batch_size_query, (int, np.int)) or self.batch_size_query <= 0:
            raise ValueError("The size of batches for querying the victim classifier must be a positive integer.")

        if not isinstance(self.nb_epochs, (int, np.int)) or self.nb_epochs <= 0:
            raise ValueError("The number of epochs must be a positive integer.")

        if not isinstance(self.nb_stolen, (int, np.int)) or self.nb_stolen <= 0:
            raise ValueError("The number of queries submitted to the victim classifier must be a positive integer.")

        if self.sampling_strategy not in ['random', 'adaptive']:
            raise ValueError("Sampling strategy must be either `random` or `adaptive`.")

        if self.reward not in ['cert', 'div', 'loss', 'all']:
            raise ValueError("Reward type must be in ['cert', 'div', 'loss', 'all'].")

        return True
