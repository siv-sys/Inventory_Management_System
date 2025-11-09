from flask import Blueprint,render_template,request,redirect,url_for,flash
from validator import validate_for_admin,get_data
from db_connect import get_db_connection
p_user_mgt = Blueprint('user_mgt',__name__,url_prefix='/user')

@p_user_mgt.route('/list')
def user_list():
    if validate_for_admin():
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE user_disable=0")
    users = cursor.fetchall()
    
    conn.close()
    return render_template('user_list.html',users=users)

@p_user_mgt.route('/create',methods=["GET","POST"])
def create_user():
    if validate_for_admin():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        nickname = request.form["nickname"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        phone = request.form["phone"].strip()
        level = request.form["level"].strip()
        user_disable = int(request.form["user_disable"].strip())
        
        if not nickname or not email or not password:
            flash("Nickname, Email, and Password are required!", "error")
            return redirect(url_for('dashboard'))
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("INSERT INTO users(nickname,email,password,phone,level,user_disable) VALUES(%s,%s,%s,%s,%s,%s)",(nickname,email,password,phone,level,user_disable))
        
        conn.commit()
        conn.close()
        
        flash("User created successfully!", "success")
        return redirect(url_for('dashboard'))
        
    return render_template('create_user.html')

@p_user_mgt.route('/edit/<int:id>',methods=["GET","POST"])
def edit_user(id):
    if validate_for_admin():
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM users WHERE userid=%s",(id,))
    user = cursor.fetchone()
    
    if request.method == 'POST':
        if request.method == 'POST':
            nickname = request.form["nickname"].strip()
            email = request.form["email"].strip()
            password = request.form["password"].strip()
            phone = request.form["phone"].strip()
            level = request.form["level"].strip()
            user_disable = int(request.form["user_disable"].strip())
        
            if not nickname or not email or not password:
                flash("Nickname, Email, and Password are required!", "error")
                return redirect(url_for('p_user_mgt.edit_user', id=id))
            
            cursor.execute("UPDATE users SET nickname=%s,email=%s,password=%s,phone=%s,level=%s,user_disable=%s WHERE userid=%s",(nickname,email,password,phone,level,user_disable,id))
            
            conn.commit()
            conn.close()
            
            flash("User updated successfully!", "success")
            return redirect(url_for('user_mgt.user_list'))
    
    conn.close()
    
    return render_template('update_user.html',user=user)
    
@p_user_mgt.route('/disable/<int:id>')
def disable_user(id):
    if validate_for_admin():
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    userid = get_data()["userid"]
    cursor.execute("UPDATE users SET user_disable=1 WHERE userid=%s AND userid <> %s",(id,userid))
    conn.commit()
    
    conn.close()
    
    flash("User deleted successfully!", "success")
    return redirect(url_for('user_mgt.user_list'))