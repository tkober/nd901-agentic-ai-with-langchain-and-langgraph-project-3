class McpToolFilter:
    def __init__(self, tools: list):
        self.tools = tools

    def by_tags(self, tags: list[str]) -> "McpToolFilter":
        """Filter MCP tools by tags."""
        filtered_tools = []
        for tool in self.tools:
            tool_tags = {
                tag.casefold()
                for tag in set(
                    tool.metadata.get("_meta", {}).get("_fastmcp", {}).get("tags", [])
                )
            }

            required_tags = {tag.casefold() for tag in tags}
            if required_tags.issubset(tool_tags):
                filtered_tools.append(tool)

        return McpToolFilter(filtered_tools)

    def by_metadata(self, key: str, value: str) -> "McpToolFilter":
        """Filter MCP tools by metadata key-value pair."""
        filtered_tools = []
        for tool in self.tools:
            tool_metadata = tool.metadata.get("_meta", {})
            if tool_metadata.get(key) == value:
                filtered_tools.append(tool)

        return McpToolFilter(filtered_tools)

    def by_author(self, author: str) -> "McpToolFilter":
        return self.by_metadata("author", author)

    def by_annotation_hint(self, hint: str, value: bool) -> "McpToolFilter":
        """Filter MCP tools by readOnlyHint annotation."""
        filtered_tools = []
        for tool in self.tools:
            hint_value = bool(tool.metadata.get(hint, False))

            if hint_value == value:
                filtered_tools.append(tool)

        return McpToolFilter(filtered_tools)

    def by_read_only(self, is_read_only: bool) -> "McpToolFilter":
        """Filter MCP tools by readOnlyHint annotation."""
        return self.by_annotation_hint("readOnlyHint", is_read_only)

    def by_name(self, name: str) -> "McpToolFilter":
        """Filter MCP tools by name."""
        filtered_tools = []
        for tool in self.tools:
            if tool.name == name:
                filtered_tools.append(tool)

        return McpToolFilter(filtered_tools)

    def get_all(self) -> list:
        return self.tools

    def get_first(self):
        return self.tools[0] if self.tools else None

    def __repr__(self):
        return "\n".join([f"{tool.name} - {tool.description}" for tool in self.tools])
