from prompt_toolkit.document import Document
from prompt_toolkit.lexers import Lexer


class BotLexer(Lexer):
    def lex_document(self, document: Document):
        def get_tokens(_line_no: int):
            tokens = document.text.split()
            result = []
            for i, token in enumerate(tokens):
                is_last = i == len(tokens) - 1
                suffix = "" if is_last and not document.text.endswith(" ") else " "
                if i == 0:
                    result.append(("class:command", token + suffix))
                elif token.startswith("--"):
                    result.append(("class:subcommand", token + suffix))
                elif token.startswith("-"):
                    result.append(("class:flag", token + suffix))
                else:
                    result.append(("class:value", token + suffix))
            return result

        return get_tokens
