from typing import Optional, List, Callable
from abc import ABC, abstractmethod
from .llvmvalue import NumberType


# https://en.wikipedia.org/wiki/Fowler%E2%80%93Noll%E2%80%93Vo_hash_function#FNV_offset_basis
FNV_OFFSET_BASIS = 0xCBF29CE484222325
# Just some big prime number
FNV_PRIME = 0x100000001B3


class SymbolTableEntry:
    def __init__(self, _identifier_name: str, _value: int, nt: NumberType):
        self.identifier_name: str = _identifier_name
        self.value: int = _value
        self.number_type: NumberType = nt

        self.next: Optional[SymbolTableEntry] = None


class SymbolTableInterface(ABC):
    def __init__(self, length: int = 512):
        pass

    @property
    @abstractmethod
    def length(self):
        pass

    @abstractmethod
    def update(
        self,
        identifier: str,
        entry: Optional[SymbolTableEntry],
    ) -> bool:
        pass

    @abstractmethod
    def get(self, identifier: str) -> Optional[SymbolTableEntry]:
        pass

    # These three methods are going to let us access SymbolTableEntries via a
    # list access operator, like symbol_table["x"]

    def __delitem__(self, key: str) -> None:
        self.update(key, None)

    def __getitem__(self, key: str) -> Optional[SymbolTableEntry]:
        return self.get(key)

    def __setitem__(self, key: str, value: Optional[SymbolTableEntry]):
        self.update(key, value)


class HashTableSymbolTable(SymbolTableInterface):
    def __init__(self, length: int = 512):
        self.data: List[Optional[SymbolTableEntry]] = [None] * length

    @property
    def length(self) -> int:
        """Length of symbol table"""
        return len(self.data)

    def resize(self, factor: int = 2) -> None:
        """Resizes symbol table by a factor of factor

        Args:
            factor (int, optional): Factor by which to expand symbol table. Defaults to 2.
        """
        self.data += [None] * factor

    def update(self, identifier: str, entry: Optional[SymbolTableEntry]) -> bool:
        """Assign a new value to an identifier

        Args:
            identifier (str): Identifier to assign to
            entry (Optional[SymbolTableEntry]): Value to assign

        Returns:
            bool: If the symbol already existed in the table
        """
        id_index = self.hash(identifier)

        symbol_already_exists = True

        if self.data[id_index] is None:
            # If there is no linked list at this position
            symbol_already_exists = False
            self.data[id_index] = entry
        else:
            # If there is a linked list at this position, we should search
            # along it to see if a matching identifier exists. If it does,
            # insert its value. Otherwise, add this new entry to the end
            # of the linked list
            linked_list_item = self.data[id_index]
            if linked_list_item:
                while linked_list_item and linked_list_item.next:
                    if linked_list_item.next.identifier_name == identifier:
                        nextnext = linked_list_item.next.next

                        if entry is None:
                            linked_list_item.next = nextnext
                        else:
                            linked_list_item.next = entry

                        if linked_list_item.next:
                            linked_list_item.next.next = nextnext
                        else:
                            linked_list_item.next = nextnext

                    linked_list_item = linked_list_item.next
                else:
                    if linked_list_item:
                        linked_list_item.next = entry
            else:
                self.data[id_index] = entry

        return symbol_already_exists

    def get(self, identifier: str) -> Optional[SymbolTableEntry]:
        """Get a value from the symbol table

        Args:
            identifier (str): Identifier mapped to output value

        Returns:
            Optional[SymbolTableEntry]: Value mapped from provided identifier
        """
        linked_list: Optional[SymbolTableEntry] = self.data[self.hash(identifier)]
        out = linked_list

        while out is not None and out.identifier_name != identifier:
            out = out.next

        return out

    def hash(self, s: str) -> int:
        """Hash function converting identifiers to hash table indices

        Args:
            s (str): String to hash

        Returns:
            int: FNV-1 value of input string
        """
        # Implementation of FNV_1A
        # Check out this post for other hashes you could implement
        # https://softwareengineering.stackexchange.com/questions/49550/which-hashing-algorithm-is-best-for-uniqueness-and-speed

        hash: int = FNV_OFFSET_BASIS

        for c in s:
            hash ^= ord(c)
            hash *= FNV_PRIME

        return hash % self.length


class FPSymbolTable(SymbolTableInterface):
    def __init__(self, length: int = 0):
        self.data: Callable[[str], Optional[SymbolTableEntry]] = self.identity_table

        self._length: int = 0

    @staticmethod
    def identity_table(s: str) -> Optional[SymbolTableEntry]:
        return None

    @property
    def length(self) -> int:
        return self._length

    def update(self, identifier: str, entry: Optional[SymbolTableEntry]) -> bool:
        symbol_already_exists: bool = self.get(identifier) is not None

        def new_symbol_table(s: str) -> Optional[SymbolTableEntry]:
            current_symbol_table = self.data

            if s == identifier:
                return entry

            return current_symbol_table(s)

        self.data = new_symbol_table

        if not symbol_already_exists and entry is not None:
            self._length += 1
        elif symbol_already_exists and entry is None:
            self._length -= 1

        return symbol_already_exists

    def get(self, identifier: str) -> Optional[SymbolTableEntry]:
        return self.data(identifier)


SymbolTable = HashTableSymbolTable
