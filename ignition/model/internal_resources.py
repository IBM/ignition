

class InternalResources:

    def __init__(self, entries=None):
        self._entries = entries if entries is not None else []
        for entry in self._entries:
            self.__validate_entry(entry)

    def __validate_entry(self, entry):
        if not isinstance(entry, InternalResourceEntry):
            raise ValueError(f'Internal resource entry should an instance of {InternalResourceEntry.__class__.__name__} but was {type(entry)}')

    def __validate_no_duplicates(self, new_entry):
        for entry in self._entries:
            if entry.name == new_entry.name:
                raise ValueError(f'Duplicate internal resource entry with name \'{entry.name}\'')

    def add(self, entry):
        self.__validate_entry(entry)
        self.__validate_no_duplicates(entry)
        self._entries.append(entry)

    def add_entry(self, identifier, name, internal_type):
        entry = InternalResourceEntry(identifier, name, internal_type)
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

    def get_by_type(self, internal_type):
        results = []
        for entry in self._entries:
            if entry.internal_type == internal_type:
                results.append(entry)
        return results

    @staticmethod
    def from_list(data):
        entries = []
        if data is not None:
            for item in data:
                entries.append(InternalResourceEntry.from_dict(item))
        return InternalResources(entries)
    
    def to_list(self):
        return [entry.to_dict() for entry in self._entries]

    def __eq__(self, other):
        if not isinstance(other, InternalResources):
            return False
        if self._entries != other._entries:
            return False
        return True

class InternalResourceEntry:

    def __init__(self, identifier, name, internal_type):
        if identifier is None:
            raise ValueError('Internal resource entry missing \'identifier\'')
        if name is None:
            raise ValueError('Internal resource entry missing \'name\'')
        if internal_type is None:
            raise ValueError('Internal resource entry missing \'internal_type\'')
        self.identifier = identifier
        self.name = name
        self.internal_type = internal_type

    @staticmethod
    def from_dict(data):
        if data is None:
            raise ValueError('Cannot convert from None')
        identifier = data.get('id')
        if identifier is None:
            raise ValueError('Internal resource entry missing \'id\'')
        name = data.get('name')
        if name is None:
            raise ValueError('Internal resource entry missing \'name\'')
        internal_type = data.get('type')
        if internal_type is None:
            raise ValueError('Internal resource entry missing \'type\'')
        return InternalResourceEntry(identifier, name, internal_type)

    def to_dict(self):
        return {
            'id': self.identifier,
            'name': self.name,
            'type': self.internal_type
        }

    def __eq__(self, other):
        if not isinstance(other, InternalResourceEntry):
            return False
        if self.identifier != other.identifier:
            return False
        if self.name != other.name:
            return False
        if self.internal_type != other.internal_type:
            return False
        return True
