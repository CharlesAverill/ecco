from typing import Optional, List, Union

# https://en.wikipedia.org/wiki/Fowler%E2%80%93Noll%E2%80%93Vo_hash_function#FNV_offset_basis
FNV_OFFSET_BASIS = 0xCBF29CE484222325
# Just some big prime number
FNV_PRIME = 0x100000001B3


class SymbolTableEntry:
    def __init__(self, _identifier_name: str, _value: int):
        self.identifier_name: str = _identifier_name
        self.value: int = _value

        self.next: Optional[SymbolTableEntry] = None


class SymbolTable:
    def __init__(self, length: int = 512):
        self.data: List[Optional[SymbolTableEntry]] = [None] * length

    @property
    def length(self):
        return len(self.data)

    def update(self, identifier: str, entry: SymbolTableEntry) -> bool:
        id_index = self.hash(identifier)

        symbol_already_exists = False

        if self.data[id_index] is None:
            symbol_already_exists = True

        self.data[id_index] = entry

        return symbol_already_exists

    def get(self, identifier: str) -> Optional[SymbolTableEntry]:
        return self.data[self.hash(identifier)]

    def hash(self, s: str) -> int:
        # Implementation of FNV_1A
        # Check out this post for other hashes you could implement
        # https://softwareengineering.stackexchange.com/questions/49550/which-hashing-algorithm-is-best-for-uniqueness-and-speed

        hash: int = FNV_OFFSET_BASIS

        for c in s:
            hash ^= ord(c)
            hash *= FNV_PRIME

        return hash % self.length

    # These three methods are going to let us access SymbolTableEntries via a
    # list access operator, like symbol_table["x"]

    def __delitem__(self, key: Union[str, int]) -> None:
        self.__setitem__(key, None)

    def __getitem__(self, key: Union[str, int]) -> Optional[SymbolTableEntry]:
        if type(key) == str:
            return self.get(key)
        elif type(key) == int:
            return self.data[key % self.length]

        return self.data[0]

    def __setitem__(self, key: Union[str, int], value: Optional[SymbolTableEntry]):
        if type(key) == str:
            self.data[self.hash(key)] = value
        elif type(key) == int:
            self.data[key % self.length] = value
