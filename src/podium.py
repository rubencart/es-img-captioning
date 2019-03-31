
import copy
import logging

logger = logging.getLogger(__name__)


class Podium(object):
    DEFAULT_BEST_ELITE = (float('-inf'), None)
    DEFAULT_BEST_PARENTS = (float('-inf'), None)

    def __init__(self, patience):
        self._best_elite = self.DEFAULT_BEST_ELITE
        self._best_parents = self.DEFAULT_BEST_PARENTS

        self._patience = patience

    def init_from_checkpt(self, models_checkpt, policy):
        self._best_elite = (models_checkpt.best_elite[0],
                            policy.from_serialized(models_checkpt.best_elite[1]))
        self._best_parents = (
            models_checkpt.best_parents[0],
            [(i, policy.from_serialized(parent)) for i, parent in models_checkpt.best_parents[1]]
        )

    def serialized(self):
        assert self._best_elite[1] is not None
        assert self._best_parents[1] is not None

        score, best_parents = self._best_parents
        return {
            'best_elite': (self._best_elite[0], self._best_elite[1].serialize()),
            'best_parents': (score, [(i, parent.serialize()) for i, parent in best_parents])
        }

    def record_elite(self, elite, acc):
        _prev_acc, _prev_elite = self._best_elite
        if not _prev_elite or acc > _prev_acc:
            self._best_elite = (acc, copy.deepcopy(elite))

    def record_parents(self, parents, score):
        best_parent_score, best_parents = self._best_parents

        if not best_parents or (score > best_parent_score):
            self._best_parents = (score, copy.deepcopy(parents))
            logger.info('GOOD GENERATION')
            return True

        elif self._patience:
            logger.info('BAD GENERATION')
            return False
        return True

    def set_best_elite(self, best_elite):
        assert not self._best_elite[1]
        self._best_elite = best_elite if best_elite else self.DEFAULT_BEST_ELITE

    def set_best_parents(self, best_parents):
        assert not self._best_parents[1]
        self._best_parents = best_parents if best_parents else self.DEFAULT_BEST_PARENTS

    def best_elite(self):
        return self._best_elite

    def best_parents(self):
        return self._best_parents