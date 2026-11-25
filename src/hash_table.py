"""개별 체이닝 해시 테이블.

칸마다 연결 리스트를 둔다. 같은 칸에 떨어진 키는 그 리스트에 이어 붙인다.
Python의 dict, set, 내장 hash()를 쓰지 않는다.
"""

R = 31


def horner_hash(key, m):
    """h <- (R * h + ord(c)) mod m. 글자마다 나머지를 취해 h가 m보다 커지지 않는다."""
    h = 0
    for c in key:
        h = (R * h + ord(c)) % m
    return h


class _Node:
    __slots__ = ("key", "value", "next")

    def __init__(self, key, value, next_node):
        self.key = key
        self.value = value
        self.next = next_node


class HashTable:
    def __init__(self, capacity=16, max_load=1.0):
        if capacity < 1:
            raise ValueError("capacity는 1 이상이어야 합니다")
        self._m = capacity
        self._n = 0
        self._max_load = max_load
        self._heads = [None] * capacity

    def __len__(self):
        return self._n

    def __contains__(self, key):
        return self._node(key)[0] is not None

    @property
    def capacity(self):
        return self._m

    @property
    def load_factor(self):
        return self._n / self._m

    def _node(self, key):
        """(key가 있는 노드 또는 None, 비교한 노드 수)"""
        node = self._heads[horner_hash(key, self._m)]
        compared = 0
        while node is not None:
            compared += 1
            if node.key == key:
                return node, compared
            node = node.next
        return None, compared

    def find(self, key):
        """(값 또는 None, 비교한 노드 수). 빈 칸이면 0이다."""
        node, compared = self._node(key)
        return (node.value if node else None), compared

    def get(self, key):
        return self.find(key)[0]

    def put(self, key, value):
        node, _ = self._node(key)
        if node is not None:
            node.value = value
            return
        i = horner_hash(key, self._m)
        self._heads[i] = _Node(key, value, self._heads[i])
        self._n += 1
        if self._max_load is not None and self.load_factor > self._max_load:
            self._resize(2 * self._m)

    def _resize(self, new_m):
        old = self._heads
        self._m = new_m
        self._n = 0
        self._heads = [None] * new_m
        for node in old:
            while node is not None:
                self.put(node.key, node.value)
                node = node.next
