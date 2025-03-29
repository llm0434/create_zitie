import logging
import os.path
import re

from PIL import Image, ImageDraw, ImageFont, ImageColor
from PyPDF2 import PdfFileMerger

from config import *

logging.basicConfig(format='%(levelname)s:%(asctime)s:%(message)s', level=logging.DEBUG)
logging.getLogger().setLevel(logging.INFO)

# 修改CHINESE_PATTERN正则表达式以保留换行符
CHINESE_PATTERN = re.compile(r'[\u4e00-\u9fa50-9\n]+')  # 新增\n支持换行符保留


class ArticleProducer(object):
    def __init__(self, article, text, author='', only_chinese=True, 
                 square_size=SQUARE_SIZE, font_size=FONT_SIZE, 
                 font_color=FONT_COLOR, table_color=TABLE_COLOR, 
                 back_color=BACK_COLOR, line=LINE, row=ROW, 
                 font_color_percent=FONT_COLOR_PERCENT,
                 font_path=FONT_PATH, pdf_dir=PDF_DIR, 
                 pic_scheme=PIC_SCHEME):
        # 修改：添加mode属性初始化
        self.mode = MODE  # 新增：从配置导入的MODE值
        
        self.article = article
        self.author = author
        self.text = text
        if only_chinese:
            self.text = ''.join(re.findall(CHINESE_PATTERN, text))
        self.square_size = square_size
        self.font_size = font_size
        self.font_color = font_color
        self.table_color = table_color
        self.back_color = back_color
        self.line = line
        self.row = row
        self.font_color_percent = font_color_percent
        self.font_path = font_path
        self.pdf_dir = pdf_dir
        self.pic_scheme = pic_scheme

        # 新增字体加载逻辑
        self.font = ImageFont.truetype(self.font_path, self.font_size)  # 新增字体初始化

        # 修改2: 使用传入参数计算颜色
        original_color = ImageColor.getrgb(font_color)
        percent = font_color_percent / 100.0
        self.fill_color = tuple(int(c * percent + 255 * (1 - percent)) for c in original_color)
        self.offset = (self.square_size - self.font_size) / 2

        # 修改3: 初始化画布时使用实例属性
        self._init_painting()
        self.pdf = PdfFileMerger()

    def _init_painting(self):
        # 修改4: 使用self的属性替代全局变量
        image = Image.new(
            self.mode,
            (self.square_size * (self.row + 2), self.square_size * (self.line + 2)),
            self.back_color
        )
        self.draw = ImageDraw.Draw(image)
        self.image = image
        self.create_table()

    def create_table(self):
        # 修改5: 使用self的属性替代全局变量
        skip = self.square_size / 2
        for x in range(self.row * 2 + 1):
            width, step = (4, 1) if x % 2 == 0 else (1, 8)
            self.draw_vertical_line(
                x=self.square_size + x * skip,
                y1=self.square_size,
                y2=(self.line + 1) * self.square_size,
                width=width,
                step=step
            )

        for y in range(self.line * 2 + 1):
            width, step = (2, 1) if y % 2 == 0 else (1, 8)
            self.draw_level_line(
                x1=self.square_size,
                x2=(self.row + 1) * self.square_size,
                y=self.square_size + y * skip,
                width=width,
                step=step
            )

    def lining(self, string):
        """
        新增换行符处理逻辑，按真实换行符分割文本并分页
        """
        lines = string.split('\n')  # 按换行符分割原始文本
        current_page = 0
        current_line_in_page = 0

        for line in lines:
            # 每行再按ROW字符数分割
            for i in range(0, len(line), self.row):  # 修改：将self.ROW改为self.row
                part = line[i:i+self.row]
                yield (current_page, current_line_in_page, part)
                current_line_in_page += 1

                # 检查是否需要换页
                if current_line_in_page % self.line == 0:  # 修改：将self.LINE改为self.line
                    current_page += 1
                    current_line_in_page = 0

    def draw_vertical_line(self, x, y1, y2, width, step=1):
        """
        画田字格中的垂线

        :param x: 横坐标
        :param y1: 纵坐标起始位置
        :param y2: 纵坐标结束位置
        :param width: 垂线宽度
        :param step: 步长，即y的上一次的结束位置和本次的起始位置，用于控制实线和虚线

        :return:
        """
        for y in range(y1, y2, step):
            self.draw.line([(x, y), (x, y + step / 2)], fill=TABLE_COLOR, width=width)

    def draw_level_line(self, x1, x2, y, width, step=1):
        """
        画田字格中的水平线

        :param x1: 横坐标起始位置
        :param x2: 横坐标结束位置
        :param y: 纵坐标
        :param width: 垂线宽度
        :param step: 步长，即x的上一次的结束位置和本次的起始位置，用于控制实线和虚线

        :return:
        """
        for x in range(x1, x2, step):
            self.draw.line([(x, y), (x + step / 2, y)], fill=TABLE_COLOR, width=width)

    def write_line(self, chars, y):
        """
        把输入文本按照行写入田字格画布

        :param chars: 当前行待写入文本
        :param y: 当前行纵坐标

        :return:
        """
        for x, ch in enumerate(chars):
            self.draw.text(
                (SQUARE_SIZE * (x + 1) + self.offset, SQUARE_SIZE * (y + 1) + self.offset),
                ch,
                font=self.font,
                fill=self.fill_color,  # 替换为动态计算的颜色
                spacing=SQUARE_SIZE
            )

    def save_image(self, page):
        """
        将画布写入文件

        :param page: 当前画布的页码

        :return: 文件存储地址
        """
        save_path = os.path.join(PDF_DIR, self.article)
        self.makedir(save_path)

        self.image.save('%s/%s.%s' % (save_path, page, PIC_SCHEME))

        logging.info('%s 转化为pdf成功！' % save_path)
        return save_path

    def paint(self):
        pics = []
        current_page = 0
        current_line_in_page = 0  # 新增初始化变量

        for page, line, text_part in self.lining(self.text):
            self.write_line(text_part, line)
            current_line_in_page = line  # 跟踪当前行号

            # 检查是否需要保存当前页
            if (line + 1) % self.line == 0:  # 修改：将self.LINE改为self.line
                path = self.save_image(current_page)
                pics.append(path)
                self._init_painting()
                current_page = page + 1

        # 处理未满一页的剩余内容
        if current_line_in_page > 0:  # 变量已正确初始化
            path = self.save_image(current_page)
            pics.append(path)

        return pics

    @staticmethod
    def get_spacings(string):
        """
        计算需要设为空格的个数（标题、作者等信息换行时使用）
        :param string:
        :return:
        """
        return ROW - len(string) % ROW

    @staticmethod
    def makedir(path):
        """
        创建目录

        :param path: 待创建目录
        :return:
        """
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def del_old_pdfs(path):
        """
        删除旧的pdf文件（当pdf合并后，即删除单页的文件及其目录）
        :param path:
        :return:
        """
        for item in os.listdir(path):
            os.remove('%s/%s' % (path, item))

        os.rmdir(path)

    def merge_pdf(self):
        """
        合并保存的单页pdf，并存储为本地文件

        :return:
        """
        path = os.path.join(PDF_DIR, self.article)

        self.makedir(path)

        dirs = os.listdir(path)
        dirs.sort()

        for item in dirs:
            self.pdf.append(os.path.join(path, item))

        pdf_dir = '{}/{}.pdf'.format(PDF_DIR, self.article)
        self.pdf.write(pdf_dir)
        self.pdf.close()  # 新增：关闭合并后的PDF文件，释放资源

        logging.info('生成pdf： {}   成功！ \n'.format(pdf_dir))

        self.del_old_pdfs(path)
