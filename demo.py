"""
满洲语翻译服务器功能演示脚本
"""
import json
import time
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from server import translation_server

console = Console()

def print_section(title):
    """打印章节标题"""
    console.print(f"\n[bold cyan]{'=' * 20} {title} {'=' * 20}[/bold cyan]")

def print_result(title, data, style="default"):
    """打印结果"""
    if style == "panel":
        console.print(Panel(str(data), title=title, border_style="cyan"))
    else:
        console.print(f"\n[bold]{title}:[/bold]")
        if isinstance(data, str):
            console.print(data)
        else:
            console.print(json.dumps(data, ensure_ascii=False, indent=2))

def print_response(title, response, show_raw=False):
    """打印API响应"""
    if show_raw:
        console.print(Panel(response.text, title=title, border_style="cyan"))
    else:
        try:
            data = response.json()
            console.print(Panel(
                json.dumps(data, ensure_ascii=False, indent=2),
                title=title,
                border_style="cyan"
            ))
        except:
            console.print(Panel(response.text, title=title, border_style="cyan"))

def test_basic_translation():
    """测试基本翻译功能"""
    print_section("1. 基础翻译功能")
    
    # 中文到满文
    console.print("[bold green]中文 -> 满文:[/bold green]")
    chinese_text = "海的人"
    manchu_text = translation_server.translate(chinese_text, source_lang="Chinese", target_lang="Manchu")
    console.print(f"输入: [yellow]{chinese_text}[/yellow]")
    console.print(f"输出: [blue]{manchu_text}[/blue]")
    
    # 满文到中文
    console.print("\n[bold green]满文 -> 中文:[/bold green]")
    manchu_text = "ᡥᠠᡳ ᡳ ᠨᡳᠶᠠᠯᠮᠠ"
    chinese_text = translation_server.translate(manchu_text, source_lang="Manchu", target_lang="Chinese")
    console.print(f"输入: [yellow]{manchu_text}[/yellow]")
    console.print(f"输出: [blue]{chinese_text}[/blue]")

def test_batch_translation():
    """测试批量翻译功能"""
    print_section("2. 批量翻译功能")
    
    # 准备测试数据
    test_sentences = [
        "ᡥᠠᡳ ᡳ ᠨᡳᠶᠠᠯᠮᠠ",
        "ᠠᠯᡳᠨ ᡳ ᠨᡳᠶᠠᠯᠮᠠ",
        "ᡥᡡᠸᠠᠩᡩᡳ ᡳ ᡥᡝᡵᡤᡝᠨ"
    ]
    
    console.print("[bold green]批量满文翻译:[/bold green]")
    results = []
    for sentence in test_sentences:
        try:
            result = translation_server.translate(sentence, source_lang="Manchu", target_lang="Chinese")
            results.append({"input": sentence, "output": result})
        except Exception as e:
            results.append({"input": sentence, "error": str(e)})
    
    for i, result in enumerate(results, 1):
        console.print(f"\n[dim]例句 {i}:[/dim]")
        console.print(f"满文: [yellow]{result['input']}[/yellow]")
        if 'output' in result:
            console.print(f"译文: [blue]{result['output']}[/blue]")
        else:
            console.print(f"错误: [red]{result['error']}[/red]")

def test_morphology_analysis():
    """测试形态分析功能"""
    print_section("3. 形态分析功能")
    
    # 测试词形态分析
    test_word = "arambi"
    console.print("[bold green]满文形态分析:[/bold green]")
    console.print(f"分析词: [yellow]{test_word}[/yellow]")
    
    try:
        # 形态分析
        analysis = translation_server.morphology.analyze_word(test_word)
        
        # 显示分析结果
        console.print("\n[bold]分析结果:[/bold]")
        console.print(Panel(
            f"词根: [blue]{analysis['root']}[/blue]\n" +
            f"词类: [blue]{analysis['word_class']}[/blue]\n\n" +
            "[bold]后缀分析:[/bold]" +
            ''.join([f"\n- {suffix['form']} ({suffix['function']})" for suffix in analysis['suffixes']]),
            border_style="cyan"
        ))
        
        # 生成注释
        gloss = translation_server.morphology.get_gloss(analysis)
        console.print(f"\n语言学注释: [green]{gloss}[/green]")
        
    except Exception as e:
        console.print(f"[red]分析错误: {str(e)}[/red]")

def test_dictionary_and_corpus():
    """测试字典和语料库功能"""
    print_section("4. 字典和语料库功能")
    
    # 词典查询
    console.print("[bold green]词典模糊查询:[/bold green]")
    queries = ["ara", "bit", "amban", "morin"]
    
    for query in queries:
        console.print(f"\n查询词: [yellow]{query}[/yellow]")
        
        try:
            matches = translation_server.dictionary.fuzzy_search(query)
            if matches:
                for match in matches[:3]:  # 显示前3个结果
                    similarity = match['similarity'] * 100
                    console.print(Panel(
                        f"[bold]匹配词:[/bold] [blue]{match['word']}[/blue]\n" +
                        f"[dim]相似度: {similarity:.1f}%[/dim]\n" +
                        f"[bold]词类:[/bold] [dim]{match['entry'].word_class}[/dim]\n" +
                        f"[bold]释义:[/bold]\n" + "\n".join([f"- {sense.get('meaning', '')}" for sense in match['entry'].senses]),
                        border_style="blue",
                        title=f"搜索结果: {query}"
                    ))
            else:
                console.print("[dim]未找到匹配结果[/dim]")
        except Exception as e:
            console.print(f"[red]查询错误: {str(e)}[/red]")
    
    # 平行语料搜索
    console.print("\n[bold green]平行语料搜索:[/bold green]")
    search_texts = [
        "ᠠᠯᡳᠨ ᡳ ᠨᡳᠶᠠᠯᠮᠠ",  # 山的人
        "ᡥᠠᡳ ᡳ ᠨᡳᠶᠠᠯᠮᠠ",  # 海的人
        "ᡥᡡᠸᠠᠩᡩᡳ ᡳ ᡥᡝᡵᡤᡝᠨ",  # 皇帝的文字
        "ᠠᠮᡠᠠᠨ ᡳ ᡠᡳᠲᡥᡝ"  # 大臣的书
    ]
    
    for search_text in search_texts:
        console.print(f"\n搜索文本: [yellow]{search_text}[/yellow]")
        
        try:
            results = translation_server.corpus.search(search_text)
            if results:
                for result in results:
                    console.print(Panel(
                        f"[bold]满文:[/bold] {result.manchu}\n" +
                        f"[bold]汉文:[/bold] {result.chinese}\n" +
                        (f"[bold]标签:[/bold] {', '.join(result.tags)}\n" if result.tags else "") +
                        f"[dim]来源: {result.source}[/dim]",
                        border_style="blue",
                        title=f"匹配结果"
                    ))
            else:
                console.print("[dim]未找到匹配结果[/dim]")
        except Exception as e:
            console.print(f"[red]搜索错误: {str(e)}[/red]")

def test_system_status():
    """测试系统状态"""
    print_section("5. 系统状态监控")
    
    # 健康检查
    console.print("[bold green]组件健康状态:[/bold green]")
    try:
        health = translation_server.health_check()
        for component, status in health['components'].items():
            status_color = "green" if status else "red"
            status_text = "正常" if status else "异常"
            console.print(f"[bold]{component}:[/bold] [{status_color}]{status_text}[/{status_color}]")
    except Exception as e:
        console.print(f"[red]健康检查错误: {str(e)}[/red]")
    
    # 性能指标
    console.print("\n[bold green]系统性能指标:[/bold green]")
    try:
        metrics = translation_server.get_metrics()
        console.print(Panel(
            f"[bold]资源使用:[/bold]\n" +
            f"CPU: [blue]{metrics['cpu_usage']:.1f}%[/blue]\n" +
            f"内存: [blue]{metrics['memory_usage']:.1f}MB[/blue]\n\n" +
            f"[bold]请求统计:[/bold]\n" +
            f"总请求: [blue]{metrics['requests']['total']}[/blue]\n" +
            f"成功率: [blue]{metrics['requests']['success']}%[/blue]\n" +
            f"平均延迟: [blue]{metrics['requests']['average_latency_ms']:.1f}ms[/blue]",
            border_style="blue"
        ))
    except Exception as e:
        console.print(f"[red]性能指标错误: {str(e)}[/red]")
    
    # 系统状态
    console.print("\n[bold green]系统整体状态:[/bold green]")
    try:
        status = translation_server.get_status()
        console.print(Panel(
            f"[bold]系统信息:[/bold]\n" +
            f"状态: [blue]{status['system']['status']}[/blue]\n" +
            f"版本: [blue]{status['system']['version']}[/blue]\n" +
            f"环境: [blue]{status['system']['environment']}[/blue]",
            border_style="green"
        ))
    except Exception as e:
        console.print(f"[red]状态检查错误: {str(e)}[/red]")

def main():
    """主函数"""
    console.print(Panel.fit(
        "[bold yellow]满洲语翻译服务器功能演示[/bold yellow]\n" +
        "[dim]展示满-汉双向翻译、形态分析、词典查询等功能[/dim]",
        border_style="cyan"
    ))
    
    try:
        # 测试所有功能
        test_basic_translation()
        test_batch_translation()
        test_morphology_analysis()
        test_dictionary_and_corpus()
        test_system_status()
        
    except Exception as e:
        console.print(f"[red]错误：{str(e)}[/red]")
        
    console.print("\n[green]演示完成！[/green]")

if __name__ == "__main__":
    main()
