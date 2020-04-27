

class AssociatedTopology:

    def __init__(self, entries=None):
        self._entries = entries if entries is not None else []
        for entry in self._entries:
            self.__validate_entry(entry)

    def __validate_entry(self, entry):
        if not isinstance(entry, AssociatedTopologyEntry):
            raise ValueError(f'Associated topology entry should an instance of {AssociatedTopologyEntry.__class__.__name__} but was {type(entry)}')

    def __validate_no_duplicates(self, new_entry):
        for entry in self._entries:
            if entry.name == new_entry.name:
                raise ValueError(f'Duplicate internal resource entry with name \'{entry.name}\'')

    def add(self, entry):
        self.__validate_entry(entry)
        self.__validate_no_duplicates(entry)
        self._entries.append(entry)

    def add_entry(self, identifier, name, element_type):
        entry = AssociatedTopologyEntry(identifier, name, element_type)
        self.__validate_no_duplicates(entry)
        self._entries.append(entry)

    def get_by_id(self, identifier):
        for entry in self._entries:
            if entry.identifier == identifier:
                return entry
        return None

    def get_by_name(self, name):
        for entry in self._entries:
            if entry.name == name:
                return entry
        return None

    def get_by_type(self, element_type):
        results = []
        for entry in self._entries:
            if entry.element_type == element_type:
                results.append(entry)
        return results

    @staticmethod
    def from_list(data):
        entries = []
        if data is not None:
            for item in data:
                entries.append(AssociatedTopologyEntry.from_dict(item))
        return AssociatedTopology(entries)
    
    def to_list(self):
        return [entry.to_dict() for entry in self._entries]

    def __eq__(self, other):
        if not isinstance(other, AssociatedTopology):
            return False
        if self._entries != other._entries:
            return False
        return True

class AssociatedTopologyEntry:

    def __init__(self, identifier, name, element_type):
        if identifier is None:
            raise ValueError('Associated topology entry missing \'identifier\'')
        if name is None:
            raise ValueError('Associated topology entry missing \'name\'')
        if element_type is None:
            raise ValueError('Associated topology entry missing \'element_type\'')
        self.identifier = identifier
        self.name = name
        self.element_type = element_type

    @staticmethod
    def from_dict(data):
        if data is None:
            raise ValueError('Cannot convert from None')
        identifier = data.get('id')
        if identifier is None:
            raise ValueError('Associated topology entry missing \'id\'')
        name = data.get('name')
        if name is None:
            raise ValueError('Associated topology entry missing \'name\'')
        element_type = data.get('type')
        if element_type is None:
            raise ValueError('Associated topology entry missing \'type\'')
        return AssociatedTopologyEntry(identifier, name, element_type)

    def to_dict(self):
        return {
            'id': self.identifier,
            'name': self.name,
            'type': self.element_type
        }

    def __eq__(self, other):
        if not isinstance(other, AssociatedTopologyEntry):
            return False
        if self.identifier != other.identifier:
            return False
        if self.name != other.name:
            return False
        if self.element_type != other.element_type:
            return False
        return True
