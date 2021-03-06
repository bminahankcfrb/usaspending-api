from abc import abstractmethod


class HierarchicalFilter:
    @classmethod
    def _query_string(cls, require, exclude) -> str:
        """Generates string in proper syntax for Elasticsearch query_string attribute, given API parameters"""
        positive_nodes = [
            cls.node(code, True, require, exclude) for code in require if cls._has_no_parents(code, require + exclude)
        ]

        negative_nodes = [
            cls.node(code, False, require, exclude) for code in exclude if cls._has_no_parents(code, require + exclude)
        ]

        positive_query = " OR ".join([node.get_query() for node in positive_nodes])
        negative_query = " AND ".join([node.get_query() for node in negative_nodes])

        if positive_query and negative_query:
            return f"{positive_query} AND {negative_query}"
        else:
            return positive_query + negative_query  # We know that exactly one is blank thanks to TinyShield

    @classmethod
    def _has_no_parents(cls, code, other_codes):
        return not len([match for match in other_codes if cls.code_is_parent_of(match, code)])

    @staticmethod
    def code_is_parent_of(code, other):
        return other[: len(code)] == code and len(code) < len(other)

    @staticmethod
    @abstractmethod
    def node(code, positive, positive_codes, negative_codes):
        pass


class Node:
    """Represents one part of the final query, either requiring or excluding one code, with any exceptions"""

    code: str
    ancestors: list
    positive: bool
    children: list

    def __init__(self, code, positive, positive_codes, negative_codes):
        self.code = code[-1]
        self.ancestors = code[:-1]
        self.positive = positive
        self.populate_children(positive_codes, negative_codes)

    def populate_children(self, positive_codes, negative_codes):
        self.children = []
        self._pop_children_helper(positive_codes, True, positive_codes, negative_codes)
        self._pop_children_helper(negative_codes, False, positive_codes, negative_codes)

    def _pop_children_helper(self, codes, is_positive, positive_codes, negative_codes):
        for other_code in codes:
            if self.is_parent_of(other_code):
                self.children.append(self.clone(other_code, is_positive, positive_codes, negative_codes))

    def get_query(self):
        retval = self._basic_search_unit()
        if not self.positive:
            retval = f"NOT {retval}"
        retval = f"({retval})"

        positive_child_query = " OR ".join([child.get_query() for child in self.children if child.positive])
        negative_child_query = " AND ".join([child.get_query() for child in self.children if not child.positive])
        joined_child_query = " AND ".join(query for query in [positive_child_query, negative_child_query] if query)

        if self.children:
            if self.positive:
                retval += f" AND ({joined_child_query})"
            else:
                retval += f" OR ({joined_child_query})"

        return f"({retval})"

    @abstractmethod
    def _basic_search_unit(self):
        pass

    def is_parent_of(self, other_path):
        return self.code in other_path[:-1]

    @abstractmethod
    def clone(self, code, positive, positive_codes, negative_codes):
        pass
