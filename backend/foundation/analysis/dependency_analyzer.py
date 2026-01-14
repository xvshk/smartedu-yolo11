"""
依赖图分析工具
基础层 - 用于分析模块间依赖关系和检测循环依赖
"""
import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import networkx as nx
import matplotlib.pyplot as plt
from dataclasses import dataclass


@dataclass
class DependencyInfo:
    """依赖信息"""
    source_module: str
    target_module: str
    import_type: str  # "import", "from_import"
    line_number: int
    is_internal: bool  # 是否为项目内部依赖


class DependencyAnalyzer:
    """依赖分析器"""
    
    def __init__(self, project_root: str = "backend"):
        self.project_root = Path(project_root)
        self.dependency_graph = nx.DiGraph()
        self.dependencies: List[DependencyInfo] = []
        self.module_files: Dict[str, Path] = {}  # 模块名 -> 文件路径映射
        
    def _build_module_mapping(self):
        """构建模块名到文件路径的映射"""
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
                
            # 转换文件路径为模块名
            relative_path = py_file.relative_to(self.project_root.parent)
            module_parts = list(relative_path.parts[:-1])  # 去掉文件名
            
            if py_file.name != "__init__.py":
                module_parts.append(py_file.stem)
            
            module_name = ".".join(module_parts)
            self.module_files[module_name] = py_file
    
    def _extract_imports(self, file_path: Path) -> List[Tuple[str, str, int]]:
        """提取文件中的导入语句"""
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append((alias.name, "import", node.lineno))
                        
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append((node.module, "from_import", node.lineno))
                        
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            
        return imports
    
    def _is_internal_module(self, module_name: str) -> bool:
        """判断是否为项目内部模块"""
        return module_name.startswith('backend.') or module_name in self.module_files
    
    def analyze_dependencies(self) -> List[DependencyInfo]:
        """分析项目依赖关系"""
        self._build_module_mapping()
        
        for module_name, file_path in self.module_files.items():
            imports = self._extract_imports(file_path)
            
            for imported_module, import_type, line_no in imports:
                is_internal = self._is_internal_module(imported_module)
                
                dependency = DependencyInfo(
                    source_module=module_name,
                    target_module=imported_module,
                    import_type=import_type,
                    line_number=line_no,
                    is_internal=is_internal
                )
                
                self.dependencies.append(dependency)
                
                # 添加到依赖图（只包含内部依赖）
                if is_internal:
                    self.dependency_graph.add_edge(module_name, imported_module)
        
        return self.dependencies
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """查找循环依赖"""
        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))
            return cycles
        except Exception as e:
            print(f"Error finding cycles: {e}")
            return []
    
    def get_dependency_layers(self) -> Dict[str, int]:
        """计算模块的依赖层级"""
        layers = {}
        
        try:
            # 使用拓扑排序计算层级
            if nx.is_directed_acyclic_graph(self.dependency_graph):
                topo_order = list(nx.topological_sort(self.dependency_graph))
                
                for i, module in enumerate(topo_order):
                    layers[module] = i
            else:
                # 如果有循环依赖，使用近似方法
                for module in self.dependency_graph.nodes():
                    # 计算到根节点的最短路径长度
                    try:
                        paths = nx.single_source_shortest_path_length(
                            self.dependency_graph.reverse(), module
                        )
                        layers[module] = max(paths.values()) if paths else 0
                    except:
                        layers[module] = 0
                        
        except Exception as e:
            print(f"Error calculating layers: {e}")
            
        return layers
    
    def get_module_metrics(self) -> Dict[str, Dict[str, int]]:
        """获取模块指标"""
        metrics = {}
        
        for module in self.dependency_graph.nodes():
            in_degree = self.dependency_graph.in_degree(module)  # 被依赖数
            out_degree = self.dependency_graph.out_degree(module)  # 依赖数
            
            metrics[module] = {
                'dependencies': out_degree,  # 该模块依赖的其他模块数
                'dependents': in_degree,     # 依赖该模块的其他模块数
                'coupling': in_degree + out_degree  # 耦合度
            }
            
        return metrics
    
    def find_problematic_modules(self) -> Dict[str, List[str]]:
        """找出有问题的模块"""
        problems = {
            'high_coupling': [],      # 高耦合模块
            'circular_deps': [],      # 参与循环依赖的模块
            'isolated': [],           # 孤立模块
            'hub_modules': []         # 中心模块（被很多模块依赖）
        }
        
        metrics = self.get_module_metrics()
        cycles = self.find_circular_dependencies()
        
        for module, metric in metrics.items():
            # 高耦合模块
            if metric['coupling'] > 10:
                problems['high_coupling'].append(module)
            
            # 中心模块
            if metric['dependents'] > 5:
                problems['hub_modules'].append(module)
            
            # 孤立模块
            if metric['coupling'] == 0:
                problems['isolated'].append(module)
        
        # 循环依赖模块
        for cycle in cycles:
            problems['circular_deps'].extend(cycle)
        
        # 去重
        for key in problems:
            problems[key] = list(set(problems[key]))
            
        return problems
    
    def generate_dependency_report(self) -> str:
        """生成依赖分析报告"""
        report = ["📊 Dependency Analysis Report", "=" * 40, ""]
        
        # 基本统计
        total_modules = len(self.module_files)
        internal_deps = len([d for d in self.dependencies if d.is_internal])
        external_deps = len([d for d in self.dependencies if not d.is_internal])
        
        report.append("📈 Basic Statistics:")
        report.append(f"  Total modules: {total_modules}")
        report.append(f"  Internal dependencies: {internal_deps}")
        report.append(f"  External dependencies: {external_deps}")
        report.append("")
        
        # 循环依赖
        cycles = self.find_circular_dependencies()
        if cycles:
            report.append(f"🔄 Circular Dependencies ({len(cycles)}):")
            for i, cycle in enumerate(cycles, 1):
                cycle_str = " -> ".join(cycle) + f" -> {cycle[0]}"
                report.append(f"  {i}. {cycle_str}")
            report.append("")
        else:
            report.append("✅ No circular dependencies found!")
            report.append("")
        
        # 问题模块
        problems = self.find_problematic_modules()
        
        if problems['high_coupling']:
            report.append(f"⚠️  High Coupling Modules ({len(problems['high_coupling'])}):")
            for module in problems['high_coupling'][:5]:  # 只显示前5个
                metrics = self.get_module_metrics()[module]
                report.append(f"  {module} (coupling: {metrics['coupling']})")
            report.append("")
        
        if problems['hub_modules']:
            report.append(f"🎯 Hub Modules ({len(problems['hub_modules'])}):")
            for module in problems['hub_modules'][:5]:
                metrics = self.get_module_metrics()[module]
                report.append(f"  {module} (dependents: {metrics['dependents']})")
            report.append("")
        
        # 层级分析
        layers = self.get_dependency_layers()
        if layers:
            max_layer = max(layers.values())
            report.append(f"📚 Dependency Layers (0-{max_layer}):")
            
            layer_counts = {}
            for module, layer in layers.items():
                layer_counts[layer] = layer_counts.get(layer, 0) + 1
            
            for layer in sorted(layer_counts.keys()):
                report.append(f"  Layer {layer}: {layer_counts[layer]} modules")
            report.append("")
        
        return "\n".join(report)
    
    def visualize_dependencies(self, output_file: str = "dependency_graph.png", 
                             max_nodes: int = 50):
        """可视化依赖图"""
        try:
            import matplotlib.pyplot as plt
            
            # 如果节点太多，只显示内部依赖最多的模块
            if len(self.dependency_graph.nodes()) > max_nodes:
                metrics = self.get_module_metrics()
                top_modules = sorted(
                    metrics.items(), 
                    key=lambda x: x[1]['coupling'], 
                    reverse=True
                )[:max_nodes]
                
                subgraph_nodes = [module for module, _ in top_modules]
                graph = self.dependency_graph.subgraph(subgraph_nodes)
            else:
                graph = self.dependency_graph
            
            plt.figure(figsize=(12, 8))
            
            # 使用层次布局
            try:
                pos = nx.spring_layout(graph, k=1, iterations=50)
            except:
                pos = nx.random_layout(graph)
            
            # 绘制节点
            nx.draw_networkx_nodes(graph, pos, node_color='lightblue', 
                                 node_size=500, alpha=0.7)
            
            # 绘制边
            nx.draw_networkx_edges(graph, pos, edge_color='gray', 
                                 arrows=True, arrowsize=20, alpha=0.5)
            
            # 绘制标签
            labels = {node: node.split('.')[-1] for node in graph.nodes()}  # 只显示最后一部分
            nx.draw_networkx_labels(graph, pos, labels, font_size=8)
            
            plt.title("Module Dependency Graph")
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Dependency graph saved to {output_file}")
            
        except ImportError:
            print("matplotlib not available, skipping visualization")
        except Exception as e:
            print(f"Error creating visualization: {e}")
    
    def export_to_dot(self, output_file: str = "dependencies.dot"):
        """导出为DOT格式（可用Graphviz渲染）"""
        try:
            nx.drawing.nx_pydot.write_dot(self.dependency_graph, output_file)
            print(f"DOT file exported to {output_file}")
            print("Use 'dot -Tpng dependencies.dot -o dependencies.png' to render")
        except Exception as e:
            print(f"Error exporting DOT file: {e}")


def main():
    """主函数"""
    analyzer = DependencyAnalyzer()
    
    print("Analyzing dependencies...")
    dependencies = analyzer.analyze_dependencies()
    
    print(analyzer.generate_dependency_report())
    
    # 可选：生成可视化
    try:
        analyzer.visualize_dependencies()
        analyzer.export_to_dot()
    except Exception as e:
        print(f"Visualization failed: {e}")


if __name__ == "__main__":
    main()