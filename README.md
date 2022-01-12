# __th-preprocessor__

Simple Thai Preprocess Functions

## __Objectives__
This repository provides simple preprocess techniques for Thai sentences/phrases

## __Supports__
The module supports Python 3.6+

## __Installation__
```
pip install th-simple-preprocessor
```

## __How to Use__
```python
from th_preprocessor.preprocess import preprocess

text = '"::::: อย่างไรก็ตามนูร์ ฮิชัม อับดุลเลาะห์ 21-09-2018 https://www.malaysiakini.com/news/444015"'
words = preprocess(text)

print(words) 
# อย่างไรก็ตามนูร์ ฮิชัม อับดุลเลาะห์ WSNUMBER WSNUMBER WSNUMBER WSLINK
```

## Package reference:
- [`th_preprocessor.preprocess.normalize_link`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L149)
- [`th_preprocessor.preprocess.normalize_at_mention`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L155)
- [`th_preprocessor.preprocess.normalize_email`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L160)
- [`th_preprocessor.preprocess.normalize_haha`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L165)
- [`th_preprocessor.preprocess.normalize_num`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L170)
- [`th_preprocessor.preprocess.normalize_phone`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L175)
- [`th_preprocessor.preprocess.normalize_accented_chars`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L180)
- [`th_preprocessor.preprocess.normalize_special_chars`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L184)
- [`th_preprocessor.preprocess.remove_hashtags`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L192)
- [`th_preprocessor.preprocess.remove_tag`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L196)
- [`th_preprocessor.preprocess.replace_dup_chars`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L206)
- [`th_preprocessor.preprocess.insert_spaces`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L231)
- [`th_preprocessor.preprocess.remove_dup_spaces`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L217)
- [`th_preprocessor.preprocess.remove_emoji`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L242)
- [`th_preprocessor.preprocess.normalize_emoji`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L246)
- [`th_preprocessor.preprocess.remove_others_char`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L250)
- [`th_preprocessor.preprocess.remove_stopwords`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L283)
- [`th_preprocessor.preprocess.preprocess`](https://github.com/wisesight/th-simple-preprocessor/blob/main/th_preprocessor/preprocess.py#L257)
## __Copyright__
All licenses in this repository are copyrighted by their respective authors. Everything else is released under CC0. See [LICENSE](https://github.com/wisesight/th-simple-preprocessor/blob/main/LICENSE) for details.
