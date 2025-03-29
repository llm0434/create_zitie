# 修改1: 添加Flask框架依赖
from flask import Flask, render_template, request, redirect, jsonify, send_from_directory
from fonts import ArticleProducer
from config import PDF_DIR

app = Flask(__name__)


# 首页
@app.route('/')
def index():
    # 修改2: 读取配置参数并传递给模板
    from config import (SQUARE_SIZE, FONT_SIZE, FONT_COLOR,
                        TABLE_COLOR, BACK_COLOR, LINE, ROW,
                        FONT_COLOR_PERCENT)
    config = {
        'square_size': SQUARE_SIZE,
        'font_size': FONT_SIZE,
        'font_color': FONT_COLOR,
        'table_color': TABLE_COLOR,
        'back_color': BACK_COLOR,
        'line': LINE,
        'row': ROW,
        'font_color_percent': FONT_COLOR_PERCENT
    }
    return render_template('index.html', config=config)


# 生成字帖
@app.route('/generate', methods=['POST'])
def generate():
    article = request.form['article']
    text = request.form['text']
    producer = ArticleProducer(
        article=article,
        text=text,
        font_color=request.form['font_color'],
        font_size=int(request.form['font_size']),
        table_color=request.form['table_color'],
        back_color=request.form['back_color'],
        line=int(request.form['line']),
        row=int(request.form['row']),
        font_color_percent=float(request.form['font_color_percent'])
    )
    producer.paint()
    producer.merge_pdf()
    
    return jsonify({
        'message': "生成成功",
        'article': producer.article
    })


# 新增下载路由
@app.route('/download/<article>')
def download(article):
    return send_from_directory(
        PDF_DIR,
        f'{article}.pdf',
        as_attachment=False,  # 允许内嵌显示
        mimetype='application/pdf'
    )


if __name__ == '__main__':
    app.run(debug=True)
