"""선형 탐지 해시 테이블.

배열 하나에 키를 직접 넣는다. 해시가 가리킨 칸이 차 있으면
빈칸이 나올 때까지 오른쪽으로 한 칸씩 가고, 끝에 닿으면 0번 칸으로 넘어간다.
인터페이스는 HashTable과 같아서 단축기에 그대로 바꿔 끼울 수 있다.
"""

from hash_table import horner_hash


class ProbingHashTable:
    def __init__(self, capacity=16, max_load=0.5):
        if capacity < 1:
            raise ValueError("capacity는 1 이상이어야 합니다")
        self._m = capacity
        self._n = 0
        self._max_load = max_load
        self._keys = [None] * capacity
        self._values = [None] * capacity

    def __len__(self):
        return self._n

    def __contains__(self, key):
        return self._slot(key)[0] is not None

    @property
    def capacity(self):
        return self._m

    @property
    def load_factor(self):
        return self._n / self._m

    def slots(self):
        """칸마다 (키, 값) 또는 None. 화면에 그릴 때 쓴다."""
        return [None if k is None else (k, v) for k, v in zip(self._keys, self._values)]

    def probe_path(self, key):
        """key를 찾을 때 들여다보는 칸 번호를 차례로 돌려준다."""
        i = horner_hash(key, self._m)
        path = []
        for _ in range(self._m):
            path.append(i)
            if self._keys[i] is None or self._keys[i] == key:
                break
            i = (i + 1) % self._m
        return path

    def _slot(self, key):
        """(key가 있는 칸 또는 None, 넣을 수 있는 빈칸 또는 None, 들여다본 칸 수)"""
        i = horner_hash(key, self._m)
        for probes in range(1, self._m + 1):
            k = self._keys[i]
            if k is None:
                return None, i, probes
            if k == key:
                return i, None, probes
            i = (i + 1) % self._m
        return None, None, self._m

    def find(self, key):
        """(값 또는 None, 들여다본 칸 수)"""
        found, _, probes = self._slot(key)
        if found is None:
            return None, probes
        return self._values[found], probes

    def get(self, key):
        return self.find(key)[0]

    def put(self, key, value):
        found, empty, _ = self._slot(key)
        if found is not None:
            self._values[found] = value
            return
        if empty is None:
            raise OverflowError("테이블이 가득 찼습니다")
        self._keys[empty] = key
        self._values[empty] = value
        self._n += 1
        if self._max_load is not None and self.load_factor > self._max_load:
            self._resize(2 * self._m)

    def _resize(self, new_m):
        old = list(zip(self._keys, self._values))
        self._m = new_m
        self._n = 0
        self._keys = [None] * new_m
        self._values = [None] * new_m
        for k, v in old:
            if k is not None:
                self.put(k, v)
