
from langfuse import Langfuse
l = Langfuse()
span = l.start_span(name="test")
print(f"SPAN METHODS: {[x for x in dir(span) if not x.startswith('_')]}")
