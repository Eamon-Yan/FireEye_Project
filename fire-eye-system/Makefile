# 火瞳系统开发工具 Makefile

.PHONY: help install dev build test clean docker-up docker-down logs db-init db-reset db-check

# 默认目标
help:
	@echo "火瞳系统开发命令:"
	@echo "  install     - 安装所有依赖"
	@echo "  dev         - 启动开发环境"
	@echo "  build       - 构建项目"
	@echo "  test        - 运行测试"
	@echo "  lint        - 代码检查"
	@echo "  format      - 代码格式化"
	@echo "  clean       - 清理临时文件"
	@echo "  docker-up   - 启动 Docker 服务"
	@echo "  docker-down - 停止 Docker 服务"
	@echo "  logs        - 查看服务日志"
	@echo "  db-init     - 初始化数据库"
	@echo "  db-reset    - 重置数据库"
	@echo "  db-check    - 检查数据库状态"

# 安装依赖
install:
	@echo "安装后端依赖..."
	cd backend && pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd frontend && npm install

# 启动开发环境
dev:
	@echo "启动开发环境..."
	docker-compose up -d neo4j redis
	@echo "等待数据库启动..."
	sleep 10
	@echo "启动后端服务..."
	cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "启动前端服务..."
	cd frontend && npm run dev

# 构建项目
build:
	@echo "构建后端..."
	cd backend && python -m build
	@echo "构建前端..."
	cd frontend && npm run build

# 运行测试
test:
	@echo "运行后端测试..."
	cd backend && python -m pytest
	@echo "运行前端测试..."
	cd frontend && npm test

# 代码检查
lint:
	@echo "后端代码检查..."
	cd backend && flake8 app/
	cd backend && mypy app/
	@echo "前端代码检查..."
	cd frontend && npm run lint

# 代码格式化
format:
	@echo "格式化后端代码..."
	cd backend && black app/
	cd backend && isort app/
	@echo "格式化前端代码..."
	cd frontend && npx prettier --write .

# 清理临时文件
clean:
	@echo "清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	cd frontend && rm -rf .next node_modules/.cache

# 启动 Docker 服务
docker-up:
	@echo "启动 Docker 服务..."
	docker-compose up -d

# 停止 Docker 服务
docker-down:
	@echo "停止 Docker 服务..."
	docker-compose down

# 查看服务日志
logs:
	docker-compose logs -f

# 重启服务
restart:
	docker-compose restart

# 查看服务状态
status:
	docker-compose ps
# 数据库管理命令
db-init:
	@echo "初始化数据库..."
	cd backend && python scripts/db_manager.py init

db-reset:
	@echo "重置数据库..."
	cd backend && python scripts/db_manager.py reset

db-check:
	@echo "检查数据库状态..."
	cd backend && python scripts/db_manager.py check

db-backup:
	@echo "备份数据库..."
	cd backend && python scripts/db_manager.py backup