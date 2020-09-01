

class AssociatedTopology:

    def __init__(self, entries=None):
        if entries is None:
            entries = {}
        for _, entry in entries.items():
            self.__validate_entry(entry)
        self._entries = entries

    def __validate_entry(self, entry):
        if not isinstance(entry, AssociatedTopologyEntry) and not isinstance(entry, RemovedTopologyEntry):
            raise ValueError(f'Associated topology entry should be an instance of {AssociatedTopologyEntry.__name__} or {RemovedTopologyEntry.__name__} but was {type(entry)}')

    def add(self, name, entry):
        self.__validate_entry(entry)
        self._entries[name] = entry

    def add_entry(self, name, element_id, element_type):
        entry = AssociatedTopologyEntry(element_id, element_type)
        self._entries[name] = entry

    def add_removed(self, name):
        entry = RemovedTopologyEntry()
        self._entries[name] = entry

    def find_id(self, element_id):
        results = {}
        for name, entry in self._entries.items():
            if not entry.removed and entry.element_id == element_id:
                results[name] = entry
        return results

    def get(self, name):
        return self._entries.get(name)

    def find_type(self, element_type):
        results = {}
        for name, entry in self._entries.items():
            if not entry.removed and entry.element_type == element_type:
                results[name] = entry
        return results

    @staticmethod
    def from_dict(data):
        entries = {}
        if data is not None:
            for name, item in data.items():
                if item == None:
                    entries[name] = RemovedTopologyEntry.from_dict(item)
                else:
                    entries[name] = AssociatedTopologyEntry.from_dict(item)
        return AssociatedTopology(entries)
    
    def to_dict(self):
        data = {}
        for name, entry in self._entries.items():
            data[name] = entry.to_dict()
        return data

    def __eq__(self, other):
        if not isinstance(other, AssociatedTopology):
            return False
        if self._entries != other._entries:
            return False
        return True

    def __str__(self):
        return f'entries: {self._entries}'

    def __repr__(self):
        return f'entries: {self._entries!r}'

class RemovedTopologyEntry:

    def __init__(self):
        self.removed = True

    @staticmethod
    def from_dict(data):
        return RemovedTopologyEntry()
            
    def to_dict(self):
        return None

    def __str__(self):
        return f'{self.__class__.__name__}()'

    def __repr__(self):
        return f'{self.__class__.__name__}()'

class AssociatedTopologyEntry:

    def __init__(self, element_id, element_type):
        if element_id is None:
            raise ValueError('Associated topology entry missing \'element_id\'')
        if element_type is None:
            raise ValueError('Associated topology entry missing \'element_type\'')
        self.element_id = element_id
        self.element_type = element_type
        self.removed = False

    @staticmethod
    def from_dict(data):
        if data is None:
            raise ValueError('Cannot convert from None')
        element_id = data.get('id')
        if element_id is None:
            raise ValueError('Associated topology entry missing \'id\'')
        element_type = data.get('type')
        if element_type is None:
            raise ValueError('Associated topology entry missing \'type\'')
        return AssociatedTopologyEntry(element_id, element_type)

    def to_dict(self):
        return {
            'id': self.element_id,
            'type': self.element_type
        }

    def __eq__(self, other):
        if not isinstance(other, AssociatedTopologyEntry):
            return False
        if self.element_id != other.element_id:
            return False
        if self.element_type != other.element_type:
            return False
        return True

    def __str__(self):
        return f'{self.__class__.__name__}(entry: {self.element_id} {self.element_type})'

    def __repr__(self):
        return f'{self.__class__.__name__}(entry: {self.element_id!r} {self.element_type!r})'
