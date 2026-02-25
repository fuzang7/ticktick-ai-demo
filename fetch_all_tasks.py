"""直接调用获取所有任务的脚本"""
import os
import sys
import logging
from dida_client import DidaClient

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# 使用与 server.py 相同的 token 文件路径
TOKEN_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".token-oauth")

def main():
    try:
        # 初始化客户端
        logger.info("初始化 DidaClient...")
        client = DidaClient(token_file=TOKEN_FILE_PATH)
        
        # 获取所有项目
        logger.info("获取所有项目...")
        projects = client.get_all_projects()
        logger.info(f"共获取到 {len(projects)} 个项目")
        
        # 获取所有任务
        logger.info("获取所有任务...")
        all_tasks_data = client.get_active_tasks_from_all_projects()
        
        # 输出摘要
        summary = all_tasks_data['summary']
        print("\n" + "="*50)
        print("任务摘要:")
        print(f"  总项目数: {summary['total_projects']}")
        print(f"  总任务数: {summary['total_tasks']}")
        print(f"  活跃任务: {summary['active_tasks']}")
        print(f"  已完成任务: {summary['completed_tasks']}")
        print(f"  有任务的项目: {summary['projects_with_tasks']}")
        print("="*50 + "\n")
        
        # 按项目分组显示任务
        project_tasks = all_tasks_data['project_tasks']
        project_map = all_tasks_data['project_map']
        
        for project_id, tasks in project_tasks.items():
            project_name = project_map.get(project_id, 'Unknown')
            active_tasks = [t for t in tasks if t.get('status', 0) in [0, 1]]
            
            if active_tasks:
                print(f"\n【{project_name}】({len(active_tasks)} 个任务)")
                print("-" * 40)
                for task in active_tasks[:10]:  # 每个项目最多显示10个
                    title = task.get('title', '无标题')
                    due_date = task.get('dueDate', '无截止日期')
                    priority = task.get('priority', 0)
                    
                    # 优先级显示
                    priority_str = {0: '', 1: '[低]', 3: '[中]', 5: '[高]'}.get(priority, '')
                    
                    print(f"  - {priority_str} {title}")
                    if due_date:
                        print(f"    截止: {due_date}")
                
                if len(active_tasks) > 10:
                    print(f"  ... 还有 {len(active_tasks) - 10} 个任务")
        
        print("\n" + "="*50)
        print(f"获取完成！共 {summary['active_tasks']} 个活跃任务")
        
    except FileNotFoundError as e:
        logger.error(f"Token 文件未找到: {e}")
        logger.info("请先运行认证脚本获取 token")
        sys.exit(1)
    except Exception as e:
        logger.error(f"获取任务失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
