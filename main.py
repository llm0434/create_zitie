import os
import sys
from fonts import ArticleProducer

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def run():
	article = input('请输入文章标题：\n')
	text = input('请输入待处理文章内容：\n')

	# 修改此处，设置only_chinese=False以保留数字等非中文字符
	producer = ArticleProducer(article=article, text=text, only_chinese=False)

	producer.paint()

	producer.merge_pdf()


if __name__ == '__main__':
	run()
