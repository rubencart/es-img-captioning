import json
import os

from algorithm.tools.experiment import ExperimentFactory
from algorithm.tools.iteration import IterationFactory
from algorithm.policies import SuppDataset, PolicyFactory
from algorithm.tools.statistics import Statistics
from algorithm.tools.utils import Config, mkdir_p


def setup_worker(exp):

    config = Config(**exp['config'])
    experiment = ExperimentFactory.create(SuppDataset(exp['dataset']), exp, config, master=False)
    policy = PolicyFactory.create(dataset=SuppDataset(exp['dataset']), exp=exp)

    return config, policy, experiment


def setup_master(exp):

    _log_dir = 'logs/{}_{}_{}_{}'.format(exp['algorithm'], exp['dataset'],
                                         exp['policy_options']['net'], os.getpid())
    mkdir_p(_log_dir)
    exp.update({'log_dir': _log_dir})

    config = Config(**exp['config'])
    iteration = IterationFactory.create(config, exp)
    experiment = ExperimentFactory.create(SuppDataset(exp['dataset']), exp, config)
    policy = PolicyFactory.create(dataset=SuppDataset(exp['dataset']), exp=exp)
    statistics = Statistics()

    if 'from_infos' in exp and exp['from_infos'] is not None:
        with open(exp['from_infos']) as f:
            infos = json.load(f)

        statistics.init_from_infos(infos)
        iteration.init_from_infos(infos)
        experiment.init_from_infos(infos)

    elif 'from_single' in exp and exp['from_single'] is not None:
        iteration.init_from_single(exp['from_single'], exp, policy)
    else:
        iteration.init_from_zero(exp, policy)

    return config, policy, statistics, iteration, experiment
