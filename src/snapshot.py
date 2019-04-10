import json
import logging
import os
import re

import torch

from experiment import Experiment
from iteration import Iteration
from policies import Policy
from statistics import Statistics
from utils import mkdir_p

logger = logging.getLogger(__name__)


def save_snapshot(stats: Statistics, it: Iteration, experiment: Experiment, policy: Policy):

    mkdir_p(experiment.snapshot_dir())

    filename = save_infos(experiment, it, stats)
    save_parents(experiment, it, stats)

    # todo necessary?
    save_elite(experiment, it, policy, stats)

    logger.info('Saved snapshot {}'.format(filename))


def save_elite(experiment, it, policy, stats):
    directory = experiment.snapshot_dir()

    # remove existing first
    elite_pattern = r'z_elite_params_e[0-9]*?_i[0-9]*?-[0-9]*?_r[.0-9]*?.pth'
    remove_existing(elite_pattern, directory)

    elite_filename = 'z_elite_params_e{e}_i{i}-{n}_r{r}.pth' \
        .format(e=it.epoch(), i=it.iteration(), n=experiment.orig_trainloader_lth(),
                r=round(stats.acc_stats()[-1], 2))
    policy.save(path=directory, filename=elite_filename)


def remove_existing(pattern, directory):
    for file in os.listdir(directory):
        if re.search(pattern, file):
            os.remove(os.path.join(directory, file))


def save_parents(experiment, it, stats):
    directory = experiment.snapshot_dir()

    # remove existing first
    parents_pattern = r'z_parents_params_e[0-9]*?_i[0-9]*?-[0-9]*?_r[.0-9]*?.tar'
    remove_existing(parents_pattern, directory)

    parents_filename = 'z_parents_params_e{e}_i{i}-{n}_r{r}.tar' \
        .format(e=it.epoch(), i=it.iteration(), n=experiment.orig_trainloader_lth(),
                r=round(stats.acc_stats()[-1], 2))
    serialized_parents = it.serialized_parents()
    torch.save(serialized_parents,
               os.path.join(directory, parents_filename))


def save_infos(experiment, it, stats):
    directory = experiment.snapshot_dir()

    infos_pattern = r'z_info_e[0-9]*?_i[0-9]*?-[0-9]*?.json'
    remove_existing(infos_pattern, directory)

    filename = 'z_info_e{e}_i{i}-{n}.json'.format(e=it.epoch(), i=it.iteration(),
                                                  n=experiment.orig_trainloader_lth())
    assert not os.path.exists(os.path.join(directory, filename))
    infos = {
        **stats.to_dict(),
        **it.to_dict(),
        **experiment.to_dict(),
    }
    with open(os.path.join(directory, filename), 'w') as f:
        json.dump(infos, f)
    return filename
