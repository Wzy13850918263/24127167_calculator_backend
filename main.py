from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# ----------------------数据库配置 SQLite----------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./calculator.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Calculator Backend")

# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库模型：计算历史表
class CalcHistory(Base):
    __tablename__ = "calc_history"
    id = Column(Integer, primary_key=True, index=True)
    expression = Column(String)
    result = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# 请求体模型
class CalcRequest(BaseModel):
    expression: str

# =====================逆波兰表达式计算核心【禁止eval，符合作业要求】=====================
def tokenize(expr: str):
    tokens = []
    i = 0
    n = len(expr)
    while i < n:
        c = expr[i]
        if c.isspace():
            i += 1
            continue
        if c in "()+-*/":
            # 处理一元负号，例如 (-5) 或 3*-2
            if c == "-":
                if i == 0 or expr[i-1] in "(+-*/":
                    tokens.append("u-")
                    i += 1
                    continue
            tokens.append(c)
            i += 1
        elif c.isdigit() or c == ".":
            j = i
            while j < n and (expr[j].isdigit() or expr[j] == "."):
                j += 1
            tokens.append(expr[i:j])
            i = j
        else:
            raise ValueError("非法字符：" + c)
    return tokens

def get_priority(op):
    if op == "u-":
        return 4
    if op in "*/":
        return 3
    if op in "+-":
        return 2
    return 0

def infix_to_postfix(tokens):
    postfix = []
    op_stack = []
    for tk in tokens:
        if tk.replace(".", "").isdigit():
            postfix.append(tk)
        elif tk == "(":
            op_stack.append(tk)
        elif tk == ")":
            while op_stack and op_stack[-1] != "(":
                postfix.append(op_stack.pop())
            if not op_stack:
                raise ValueError("括号不匹配")
            op_stack.pop()
        else:
            while op_stack and get_priority(op_stack[-1]) >= get_priority(tk):
                postfix.append(op_stack.pop())
            op_stack.append(tk)
    while op_stack:
        top = op_stack.pop()
        if top == "(":
            raise ValueError("括号不匹配")
        postfix.append(top)
    return postfix

def calc_postfix(postfix):
    st = []
    for tk in postfix:
        if tk == "u-":
            val = st.pop()
            st.append(-float(val))
        elif tk in "+-*/":
            b = float(st.pop())
            a = float(st.pop())
            if tk == "+":
                res = a + b
            elif tk == "-":
                res = a - b
            elif tk == "*":
                res = a * b
            elif tk == "/":
                if abs(b) < 1e-9:
                    raise ZeroDivisionError("除数不能为零")
                res = a / b
            st.append(res)
        else:
            st.append(tk)
    if len(st) != 1:
        raise ValueError("表达式非法")
    return st[0]

def calculate_expression(expr: str):
    tokens = tokenize(expr)
    post = infix_to_postfix(tokens)
    return calc_postfix(post)

# =====================API接口=====================
# 计算接口 POST
@app.post("/api/calculate")
def calc(req: CalcRequest):
    db = SessionLocal()
    try:
        res = calculate_expression(req.expression)
        record = CalcHistory(expression=req.expression, result=res)
        db.add(record)
        db.commit()
        db.refresh(record)
        return {"success": True, "expression": req.expression, "result": res}
    except ZeroDivisionError:
        return {"success": False, "message": "除数不能为零"}
    except Exception as e:
        return {"success": False, "message": "表达式错误：" + str(e)}
    finally:
        db.close()

# 获取全部历史 GET
@app.get("/api/history")
def get_history():
    db = SessionLocal()
    records = db.query(CalcHistory).order_by(CalcHistory.id.desc()).all()
    db.close()
    data = []
    for r in records:
        data.append({
            "id": r.id,
            "expression": r.expression,
            "result": r.result,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return {"history": data}

# 删除单条历史 DELETE
@app.delete("/api/history/{hid}")
def del_history(hid: int):
    db = SessionLocal()
    item = db.query(CalcHistory).filter(CalcHistory.id == hid).first()
    if not item:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(item)
    db.commit()
    db.close()
    return {"success": True, "msg": "删除成功"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
