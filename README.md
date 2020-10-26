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
# ['อย่างไรก็ตาม', 'นูร์', 'ฮิ', 'ชัม', 'อับ', 'ดุล', 'เลาะ', 'ห์', 'wsnumber', 'wsnumber', 'wsnumber', 'wsurl']
```

## __Copyright__
All licenses in this repository are copyrighted by their respective authors. Everything else is released under CC0. See [LICENSE](https://github.com/wisesight/th-simple-preprocessor/blob/main/LICENSE) for details.