"""
Harnesses set up resources and values in the environment when they are needed
and then tear down those resources when they're no longer needed. A Harness
is simply a Python context manager[1]. You may be interested in using
contextlib[2] to create a Harness.

A harness outputs a dictionary. You can use the Harness class to wrap a naive
context manager so that it emits an Environment including your harness's
output.

[1] https://docs.python.org/3/reference/datamodel.html#context-managers
[2] https://docs.python.org/3/library/contextlib.html
"""

from .context import Context


class Harness:
    def __init__(self, context_manager, context={}):
        self.context = Context(**context)

        if isinstance(context_manager, list):
            self.cm = [cm for cm in context_manager]
        else:
            self.cm = context_manager

    def _update_context(self, context, context_update):
        updated_context = context
        for key, value in context_update.items():
            if key not in context:
                updated_context[key] = value
            elif isinstance(context[key], list):
                updated_context[key] = [*context[key], *value]
            elif isinstance(context[key], dict):
                updated_context[key] = self._update_context(
                    context=context[key], context_update=value
                )
            else:
                updated_context[key] = [context[key], value]

        return updated_context

    def __enter__(self):
        if isinstance(self.cm, list):
            for cm in self.cm:
                values = cm.__enter__()
                if values:
                    self.context = self._update_context(
                        context=self.context, context_update=values
                    )
        else:
            values = self.cm.__enter__()
            if values:
                self.context = self._update_context(
                    context=self.context, context_update=values
                )

        return self.context

    def __exit__(self, *exc):
        if isinstance(self.cm, list):
            for cm in self.cm:
                cm.__exit__(*exc)
        else:
            self.cm.__exit__(*exc)
