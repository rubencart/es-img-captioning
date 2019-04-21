import logging
import os
import time

import torch

from algorithm.tools.utils import find_file_with_pattern


logger = logging.getLogger(__name__)


class Sensitivity(object):

    def __init__(self, net):
        self.sensitivity = None
        self.net = net

    def get_sensitivity(self):
        return self.sensitivity

    def set_sensitivity(self, task_id, parent_id, experiences, directory, underflow, method):
        sensitivity_filename = 'sens_t{t}_p{p}.txt'.format(t=task_id, p=parent_id)
        if find_file_with_pattern(sensitivity_filename, directory):
            # logger.info('Loaded sensitivity for known parent')
            self.sensitivity = torch.load(os.path.join(directory, sensitivity_filename))
        else:
            # if self.orig_batch_size == 0:
            #     # todo doesn't work for capt
            #     self.orig_batch_size = experiences.size(0)

            start_time = time.time()
            torch.set_grad_enabled(True)
            for param in self.net.parameters():
                param.requires_grad = True

            sensitivity, batch_size = self._calc_sensitivity(experiences, method)
            sensitivity[sensitivity < underflow] = underflow

            torch.set_grad_enabled(False)
            for param in self.net.parameters():
                param.requires_grad = False
            for param in sensitivity:
                param.requires_grad = False

            time_elapsed = time.time() - start_time
            logger.info('Safe mutation sensitivity computed in {:.2f}s on {} samples'
                        .format(time_elapsed, batch_size))
            torch.save(sensitivity.clone().detach().requires_grad_(False),
                       os.path.join(directory, sensitivity_filename))
            self.sensitivity = sensitivity.clone().detach().requires_grad_(False)
            logger.info('Sensitivity parent {}: min {:.2f}, mean {:.2f}, max {:.2f}'
                        .format(parent_id, sensitivity.min().item(), sensitivity.mean().item(),
                                sensitivity.max().item()))
            del sensitivity, experiences

    def _calc_sensitivity(self, experiences, method):
        from algorithm.policies import Mutation
        if method == Mutation.SAFE_GRAD_SUM:
            return self._calc_sum_sensitivity(experiences)
        elif method == Mutation.SAFE_GRAD_ABS:
            return self._calc_abs_sensitivity(experiences)

    def _calc_sum_sensitivity(self, experiences):
        old_output = self.net._contained_forward(experiences)
        num_outputs = old_output.size(1)
        batch_size = old_output.size(0)

        jacobian = torch.zeros(num_outputs, self.net.nb_params)
        grad_output = torch.zeros(*old_output.size())

        for k in range(num_outputs):
            self.net.zero_grad()
            grad_output.zero_()
            grad_output[:, k] = 1.0

            old_output.backward(gradient=grad_output, retain_graph=True)
            jacobian[k] = self.net._extract_grad()
        self.net.zero_grad()

        sensitivity = torch.sqrt((jacobian ** 2).sum(0))  # * proportion

        copy = sensitivity.clone().detach().requires_grad_(False)
        del old_output, jacobian, grad_output, experiences, num_outputs, sensitivity
        return copy, batch_size

    def _calc_abs_sensitivity(self, experiences):

        old_output = self.net._contained_forward(experiences)
        num_outputs = old_output.size(1)
        batch_size = old_output.size(0)

        jacobian = torch.zeros(num_outputs, self.nb_params, batch_size)
        grad_output = torch.zeros((1, num_outputs))

        for k in range(num_outputs):
            for i in range(batch_size):
                old_output_i = self.net._contained_forward(experiences, i=i)

                self.net.zero_grad()
                grad_output.zero_()
                grad_output[0, k] = 1.0

                old_output_i.backward(gradient=grad_output, retain_graph=True)
                jacobian[k, :, i] = self.net._extract_grad()

        self.net.zero_grad()

        jacobian = torch.abs(jacobian).mean(2)
        sensitivity = torch.sqrt((jacobian ** 2).sum(0))

        copy = sensitivity.clone().detach().requires_grad_(False)
        del old_output, jacobian, grad_output, experiences, num_outputs, sensitivity
        return copy, batch_size

    def _calc_second_sensitivity(self):
        raise NotImplementedError