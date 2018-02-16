from enchant import Dict
from enchant.checker import SpellChecker
from enchant.tokenize import EmailFilter, URLFilter

from cloudbot import hook

locale = "en_US"
en_dict = Dict(locale)


@hook.command()
def spell(text):
    """<word/sentence> - Check spelling of a word or sentence."""
    if len(text.split(" ")) > 1:
        # input is a sentence
        checker = SpellChecker(en_dict, filters=[EmailFilter, URLFilter])
        checker.set_text(text)

        is_correct = True
        offset = 0
        for err in checker:
            is_correct = False
            # find the location of the incorrect word
            start = err.wordpos + offset
            finish = start + len(err.word)
            # get some suggestions for it
            suggestions = err.suggest()
            s_string = '/'.join(suggestions[:3])
            s_string = "[h1]{}[/h1]".format(s_string)
            # calculate the offset for the next word
            offset = (offset + len(s_string)) - len(err.word)
            # replace the word with the suggestions
            text = text[:start] + s_string + text[finish:]
        return "$(green)Correct$(c)" if is_correct else text
    else:
        # input is a word
        is_correct = en_dict.check(text)
        suggestions = en_dict.suggest(text)
        s_string = ', '.join(suggestions[:10])
        return '"{}" appears to be {} [div] [h1]Similar:[/h1] {}'.format(
            text,
            "$(green)correct$(c)" if is_correct else "$(red)incorrect$(c)",
            s_string)

