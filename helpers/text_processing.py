from difflib import SequenceMatcher
from re import escape
from typing import Dict, Tuple

from pandas import DataFrame, Series


def matches_n_consecutive_words(text: str, database: set, consecutive_n: int):
    """Check whether a phrase (one or more words separated by whitespace characters)

    from given database (set of phrases) is present in the provided text quickly.
    Return the first matched phrase.
    """
    words = text.split()
    for span_size in range(1, consecutive_n + 1):
        for start_position in range(0, len(words)):
            if start_position + span_size <= len(words):
                substring = ' '.join(words[start_position:start_position + span_size])
                if substring in database:
                    return substring
    return None


def highlight_first(text: str, keyword: str, margin: int = 50):
    pos = text.index(keyword)
    return text[max(0, pos - margin):min(pos + margin, len(text))]


def check_usage(term, data: DataFrame, column: str, words=True, highlight=None):
    # \b = a word break
    search_term = fr'\b{escape(term)}\b' if words else term
    highlight = highlight if highlight else term
    return data[data[column].str.contains(search_term)][column].apply(highlight_first, keyword=highlight)


def sequence_similarity_ratio(a: str, b: str):
    return SequenceMatcher(a=a, b=b, autojunk=False).ratio()


def find_term_typos(term_counts: Series, threshold: int):
    typos_terms_check = DataFrame([
        {
            'rare_term': term,
            'popular_term': suggested_term,
            'similarity': sequence_similarity_ratio(term, suggested_term)
        }
        for term in term_counts[term_counts < threshold].index
        for suggested_term in term_counts[term_counts >= threshold].index
    ])
    potential_typos = (
        typos_terms_check[typos_terms_check.similarity > 0.9]
        .sort_values(['similarity', 'popular_term', 'rare_term'], ascending=False)
        .reset_index(drop=True)
    )
    return potential_typos


def create_typos_map(
    potential_typos: DataFrame,
    is_typo: Dict[Tuple[str, str], bool]
) -> Dict[str, str]:
    """Create a mapping of rare_term → popular term

    Args:
        potential_typos: a frame returned by find_term_typos
        is_typo: manual mapping of tuple (rare_term, popular_term) to boolean values
    """
    assert (
        set(is_typo.keys())
        ==
        set(potential_typos[['rare_term', 'popular_term']].apply(tuple, axis=1))
    )
    return {
        rare_term: term
        for (rare_term, term), need_changing in is_typo.items()
        if need_changing
    }


def prefix_remover(prefix: str, enforce=True):
    def remove_prefix(text: str):
        if text.startswith(prefix):
            return text[len(prefix):]
        else:
            if enforce:
                raise ValueError(f'Prefix {prefix!r} missing in {text!r}')
            else:
                return text
    return remove_prefix
