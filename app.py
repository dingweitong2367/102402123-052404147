import sqlite3
import datetime
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)
DATABASE = 'lost_found.db'

# 当前模拟登录用户
CURRENT_USER = {
    "id": 1,
    "username": "刘同学"
}

# ---------------------- 数据库工具 ----------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        c = db.cursor()
        
        # 用户表
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL
        )''')
        
        # 物品表（新增联系方式字段）
        c.execute('''CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            item_type TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            time TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT '进行中',
            user_id INTEGER NOT NULL,
            publish_time TEXT NOT NULL,
            view_count INTEGER DEFAULT 0,
            phone TEXT,
            wechat TEXT,
            qq TEXT
        )''')
        
        # 通知表
        c.execute('''CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            item_id INTEGER,
            create_time TEXT NOT NULL,
            is_read INTEGER DEFAULT 0
        )''')
        
        # 搜索历史表
        c.execute('''CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            keyword TEXT NOT NULL,
            create_time TEXT NOT NULL
        )''')

        # 插入测试用户
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO users (username) VALUES (?)", ("陈同学",))
            c.execute("INSERT INTO users (username) VALUES (?)", ("刘同学",))
            c.execute("INSERT INTO users (username) VALUES (?)", ("王同学",))
            c.execute("INSERT INTO users (username) VALUES (?)", ("李同学",))

        # 插入测试物品数据（含联系方式）
        c.execute("SELECT COUNT(*) FROM items")
        if c.fetchone()[0] == 0:
            now = datetime.datetime.now()
            items = [
                ("无线耳机", "招领", "数码", "运动场东侧看台第3排", "今天09:45", "白色充电仓,右耳有一处小划痕,捡到时放在座位上。", "进行中", 1, (now - datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"), 12, "13812342333", "chen_stu_2026", "2634123456"),
                ("校园卡", "寻物", "证件", "食堂", "今天08:20", "卡套有蓝色卡贴", "进行中", 4, (now - datetime.timedelta(hours=4)).strftime("%Y-%m-%d %H:%M"), 8, "13623456789", "li_stu_2026", "2634098765"),
                ("宿舍钥匙串", "寻物", "钥匙", "教学楼A栋", "昨天18:30", "带蓝色小熊挂件", "进行中", 2, (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), 15, "13987654321", "liu_stu_2026", "2634987654"),
                ("折叠雨伞", "招领", "其他", "图书馆", "昨天15:00", "黑色长柄伞", "已归还", 1, (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), 20, "13812342333", "chen_stu_2026", "2634123456"),
                ("高等数学教材", "招领", "书籍", "图书馆三楼自习室", "2天前", "书内有笔记", "进行中", 3, (now - datetime.timedelta(days=2)).strftime("%Y-%m-%d %H:%M"), 5, "13756781234", "wang_stu_2026", "2634567890"),
                ("保温杯", "寻物", "其他", "食堂", "3天前", "银色杯身,红色杯盖", "进行中", 2, (now - datetime.timedelta(days=3)).strftime("%Y-%m-%d %H:%M"), 10, "13987654321", "liu_stu_2026", "2634987654"),
                ("智能手表", "寻物", "数码", "体育馆", "昨天20:10", "黑色表带", "进行中", 2, (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), 7, "13987654321", "liu_stu_2026", "2634987654"),
                ("充电宝", "招领", "数码", "教学楼C栋", "3天前", "银色1万毫安", "进行中", 3, (now - datetime.timedelta(days=3)).strftime("%Y-%m-%d %H:%M"), 3, "13756781234", "wang_stu_2026", "2634567890"),
            ]
            for item in items:
                c.execute('''INSERT INTO items 
                    (title, item_type, category, location, time, description, status, user_id, publish_time, view_count, phone, wechat, qq)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', item)

        # 插入测试通知
        c.execute("SELECT COUNT(*) FROM notifications")
        if c.fetchone()[0] == 0:
            now = datetime.datetime.now()
            notis = [
                (2, "认领提醒", "有同学对你发布的「无线耳机」发起了认领申请", 1, (now - datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"), 0),
                (2, "浏览提醒", "你发布的「宿舍钥匙串」今日被浏览12次", 3, (now - datetime.timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"), 0),
                (2, "状态更新", "你认领的「折叠雨伞」已标记为「已归还」", 4, (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), 0),
                (2, "发布成功", "「无线耳机」信息已通过审核,展示在列表", 1, (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), 0),
            ]
            for n in notis:
                c.execute('''INSERT INTO notifications (user_id, type, content, item_id, create_time, is_read)
                    VALUES (?,?,?,?,?,?)''', n)

        db.commit()

# 手机号脱敏工具
def mask_phone(phone):
    if phone and len(phone) >= 11:
        return phone[:3] + "****" + phone[-4:]
    return phone

# QQ号脱敏
def mask_qq(qq):
    if qq and len(qq) >= 8:
        return qq[:4] + "******"
    return qq

# ---------------------- 页面路由 ----------------------

# 1. 首页
@app.route('/')
def index():
    db = get_db()
    latest = db.execute("SELECT items.*, users.username FROM items JOIN users ON items.user_id = users.id ORDER BY publish_time DESC LIMIT 4").fetchall()
    categories = ["证件", "书籍", "钥匙", "数码", "衣物", "其他"]
    return render_template('index.html', latest=latest, categories=categories, user=CURRENT_USER)

# 2. 搜索界面
@app.route('/search')
def search():
    keyword = request.args.get('q', '').strip()
    db = get_db()
    results = []
    if keyword:
        db.execute("INSERT INTO search_history (user_id, keyword, create_time) VALUES (?, ?, ?)",
                   (CURRENT_USER["id"], keyword, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        db.commit()
        results = db.execute('''SELECT items.*, users.username FROM items 
            JOIN users ON items.user_id = users.id 
            WHERE items.title LIKE ? OR items.location LIKE ? OR items.description LIKE ?
            ORDER BY publish_time DESC''', 
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%")).fetchall()
    
    hot_words = ["钥匙", "耳机", "雨伞", "水杯", "校园卡"]
    history = db.execute("SELECT DISTINCT keyword FROM search_history WHERE user_id = ? ORDER BY create_time DESC LIMIT 10", 
                         (CURRENT_USER["id"],)).fetchall()
    return render_template('search.html', 
                         keyword=keyword, 
                         results=results, 
                         hot_words=hot_words, 
                         history=history,
                         user=CURRENT_USER)

# 清空搜索历史
@app.route('/search/clear')
def clear_history():
    db = get_db()
    db.execute("DELETE FROM search_history WHERE user_id = ?", (CURRENT_USER["id"],))
    db.commit()
    return redirect(url_for('search'))

# 3. 分类浏览
@app.route('/category/<category>')
def category(category):
    db = get_db()
    sub_cats = {
        "数码": ["全部", "耳机", "充电宝", "数据线", "手表"],
        "证件": ["全部", "校园卡", "身份证", "学生证"],
        "钥匙": ["全部", "宿舍钥匙", "教室钥匙", "车钥匙"],
        "书籍": ["全部", "教材", "课外书", "笔记本"],
        "衣物": ["全部", "外套", "帽子", "雨伞"],
        "其他": ["全部", "水杯", "文具", "其他"]
    }
    sub_list = sub_cats.get(category, ["全部"])
    
    items = db.execute('''SELECT items.*, users.username FROM items 
        JOIN users ON items.user_id = users.id 
        WHERE items.category = ?
        ORDER BY publish_time DESC''', (category,)).fetchall()
    
    return render_template('category.html', 
                         category=category, 
                         sub_cats=sub_list, 
                         items=items,
                         user=CURRENT_USER)

# 4. 物品详情
@app.route('/item/<int:item_id>')
def item_detail(item_id):
    db = get_db()
    db.execute("UPDATE items SET view_count = view_count + 1 WHERE id = ?", (item_id,))
    db.commit()
    
    item = db.execute('''SELECT items.*, users.username
        FROM items JOIN users ON items.user_id = users.id 
        WHERE items.id = ?''', (item_id,)).fetchone()
    
    if not item:
        return "物品不存在", 404
    
    masked_phone = mask_phone(item['phone'])
    is_owner = (item['user_id'] == CURRENT_USER['id'])
    
    return render_template('detail.html', 
                         item=item, 
                         masked_phone=masked_phone,
                         is_owner=is_owner,
                         user=CURRENT_USER)

# 5. 联系发布者
@app.route('/contact/<int:item_id>')
def contact_publisher(item_id):
    db = get_db()
    item = db.execute('''SELECT items.*, users.username
        FROM items JOIN users ON items.user_id = users.id 
        WHERE items.id = ?''', (item_id,)).fetchone()
    
    if not item:
        return "物品不存在", 404
    
    masked_phone = mask_phone(item['phone'])
    masked_qq = mask_qq(item['qq'])
    
    return render_template('contact.html', 
                         item=item, 
                         masked_phone=masked_phone,
                         masked_qq=masked_qq,
                         user=CURRENT_USER)

# 6. 消息通知
@app.route('/notifications')
def notifications():
    db = get_db()
    db.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (CURRENT_USER["id"],))
    db.commit()
    
    notis = db.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY create_time DESC", 
                       (CURRENT_USER["id"],)).fetchall()
    return render_template('notifications.html', notifications=notis, user=CURRENT_USER)

# 7. 全部信息
@app.route('/all')
def all_items():
    filter_type = request.args.get('type', '全部')
    db = get_db()
    
    if filter_type == '寻物':
        items = db.execute('''SELECT items.*, users.username FROM items 
            JOIN users ON items.user_id = users.id 
            WHERE item_type = '寻物'
            ORDER BY publish_time DESC''').fetchall()
    elif filter_type == '招领':
        items = db.execute('''SELECT items.*, users.username FROM items 
            JOIN users ON items.user_id = users.id 
            WHERE item_type = '招领'
            ORDER BY publish_time DESC''').fetchall()
    else:
        items = db.execute('''SELECT items.*, users.username FROM items 
            JOIN users ON items.user_id = users.id 
            ORDER BY publish_time DESC''').fetchall()
    
    return render_template('all_items.html', items=items, current_type=filter_type, user=CURRENT_USER)

# 8. 发布信息
@app.route('/publish', methods=['GET', 'POST'])
def publish():
    if request.method == 'POST':
        item_type = request.form['item_type']
        title = request.form['title']
        category = request.form['category']
        location_time = request.form['location_time']
        description = request.form['description']
        # 接收表单填写的联系方式
        phone = request.form.get('phone', '')
        wechat = request.form.get('wechat', '')
        qq = request.form.get('qq', '')
        
        db = get_db()
        cursor = db.execute('''INSERT INTO items 
            (title, item_type, category, location, time, description, status, user_id, publish_time, view_count, phone, wechat, qq)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (title, item_type, category, 
             location_time.split('·')[0] if '·' in location_time else location_time, 
             location_time.split('·')[1] if '·' in location_time else "今天", 
             description, "进行中", CURRENT_USER["id"], 
             datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 0,
             phone, wechat, qq))
        db.commit()
        
        new_id = cursor.lastrowid
        db.execute('''INSERT INTO notifications (user_id, type, content, item_id, create_time, is_read)
            VALUES (?,?,?,?,?,?)''',
            (CURRENT_USER["id"], "发布成功", f"「{title}」信息已通过审核,展示在列表", 
             new_id, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 0))
        db.commit()
        
        return redirect(url_for('publish_success'))
    
    categories = ["钥匙", "数码", "书籍", "衣物", "证件", "其他"]
    return render_template('publish.html', categories=categories, user=CURRENT_USER)

@app.route('/publish/success')
def publish_success():
    return render_template('publish_success.html', user=CURRENT_USER)

# 9. 我的发布
@app.route('/my/posts')
def my_posts():
    filter_status = request.args.get('status', '全部')
    db = get_db()
    
    query = "SELECT * FROM items WHERE user_id = ?"
    params = [CURRENT_USER["id"]]
    
    if filter_status == '进行中':
        query += " AND status = '进行中'"
    elif filter_status == '已归还':
        query += " AND status = '已归还'"
    
    query += " ORDER BY publish_time DESC"
    items = db.execute(query, params).fetchall()
    
    total = db.execute("SELECT COUNT(*) FROM items WHERE user_id = ?", (CURRENT_USER["id"],)).fetchone()[0]
    returned = db.execute("SELECT COUNT(*) FROM items WHERE user_id = ? AND status = '已归还'", (CURRENT_USER["id"],)).fetchone()[0]
    ongoing = db.execute("SELECT COUNT(*) FROM items WHERE user_id = ? AND status = '进行中'", (CURRENT_USER["id"],)).fetchone()[0]
    
    return render_template('my_posts.html', 
                         items=items, 
                         current_status=filter_status,
                         total=total,
                         returned=returned,
                         ongoing=ongoing,
                         user=CURRENT_USER)

# 10. 修改状态
@app.route('/my/posts/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_status(item_id):
    db = get_db()
    item = db.execute("SELECT * FROM items WHERE id = ? AND user_id = ?", 
                      (item_id, CURRENT_USER["id"])).fetchone()
    
    if not item:
        return "无权操作", 403
    
    if request.method == 'POST':
        new_status = request.form['status']
        db.execute("UPDATE items SET status = ? WHERE id = ?", (new_status, item_id))
        db.commit()
        return redirect(url_for('edit_success', item_id=item_id))
    
    return render_template('edit_status.html', item=item, user=CURRENT_USER)




