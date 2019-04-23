import json
import os

from algorithm.tools.experiment import ExperimentFactory
from algorithm.tools.iteration import Iteration
from algorithm.policies import SuppDataset, PolicyFactory, Net
from algorithm.tools.statistics import Statistics
from algorithm.tools.utils import Config, mkdir_p


def setup_worker(exp):
    assert exp['mode'] in ['seeds', 'nets'], '{}'.format(exp['mode'])

    config = Config(**exp['config'])
    experiment = ExperimentFactory.create(SuppDataset(exp['dataset']), exp, config, None, master=False)
    policy = PolicyFactory.create(dataset=SuppDataset(exp['dataset']), mode=exp['mode'], exp=exp)

    # experiment.init_loaders(config=config, exp=exp)
    # elite = policy.generate_model()
    # policy.init_model(policy.generate_model())
    return config, policy, experiment


def setup_master(exp):
    assert exp['mode'] in ['seeds', 'nets'], '{}'.format(exp['mode'])

    _log_dir = 'logs/es_{}_{}_{}_{}'.format(exp['dataset'], exp['policy_options']['net'], exp['mode'], os.getpid())
    mkdir_p(_log_dir)
    exp.update({'log_dir': _log_dir})

    config = Config(**exp['config'])
    iteration = Iteration(config, exp)
    # todo when init from infos experiment will still take batch size from exp.json and not
    # from infos!!!
    experiment = ExperimentFactory.create(SuppDataset(exp['dataset']), exp, config, iteration)
    policy = PolicyFactory.create(dataset=SuppDataset(exp['dataset']), mode=exp['mode'], exp=exp)
    statistics = Statistics()

    if 'from_population' in exp and exp['from_population'] is not None:

        with open(exp['from_population']) as f:
            infos = json.load(f)

        statistics.init_from_infos(infos)
        iteration.init_from_infos(infos)
        experiment.init_from_infos(infos)
        # experiment.init_loaders(batch_size=iteration.batch_size(), exp=exp)

    elif 'from_single' in exp and exp['from_single'] is not None:
        iteration.init_from_single(exp['from_single'], exp['truncation'], exp['num_elite_cands'], policy)
        # experiment.init_loaders(config=config, exp=exp)
    else:
        iteration.init_parents(exp['truncation'], exp['num_elite_cands'], policy)
        # experiment.init_loaders(config=config, exp=exp)

    # policy.init_model(policy.generate_model())
    # policy.set_model(iteration.elite())
    return config, policy, statistics, iteration, experiment
