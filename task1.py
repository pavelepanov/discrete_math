from collections import Counter
from html import escape
from math import ceil, log2
from pathlib import Path
import csv


TEXT = """
ОНА ЗАБОТЛИВО ПОГЛЯДЫВАЛА НА НЕГО В ТО ВРЕМЯ КАК ОН ПОДОШЕЛ ПОСЛУШАТЬ ТО ЧТО ГОВОРИЛОСЬ ОКОЛО МОРТЕМАРА И ОТОШЕЛ К ДРУГОМУ КРУЖКУ ГДЕ ГОВОРИЛ АББАТ ДЛЯ ПЬЕРА ВОСПИТАННОГО ЗА ГРАНИЦЕЙ ЭТОТ ВЕЧЕР АННЫ ПАВЛОВНЫ БЫЛ ПЕРВЫЙ КОТОРЫЙ ОН ВИДЕЛ В РОССИИ ОН ЗНАЛ ЧТО ТУТ СОБРАНА ВСЯ ИНТЕЛЛИГЕНЦИЯ ПЕТЕРБУРГА И У НЕГО КАК У РЕБЕНКА В ИГРУШЕЧНОЙ ЛАВКЕ РАЗБЕГАЛИСЬ ГЛАЗА ОН ВСЕ БОЯЛСЯ ПРОПУСТИТЬ УМНЫЕ РАЗГОВОРЫ КОТОРЫЕ ОН МОЖЕТ УСЛЫХАТЬ ГЛЯДЯ НА УВЕРЕННЫЕ И ИЗЯЩНЫЕ ВЫРАЖЕНИЯ ЛИЦ СОБРАННЫХ ЗДЕСЬ ОН ВСЕ ЖДАЛ ЧЕГО НИБУДЬ ОСОБЕННО УМНОГО НАКОНЕЦ ОН ПОДОШЕЛ К МОРИО РАЗГОВОР ПОКАЗАЛСЯ ЕМУ ИНТЕРЕСЕН И ОН ОСТАНОВИЛСЯ ОЖИДАЯ СЛУЧАЯ ВЫСКАЗАТЬ СВОИ МЫСЛИ КАК ЭТО ЛЮБЯТ МОЛОДЫЕ ЛЮДИ
""".strip()


BASE_DIR = Path(__file__).resolve().parent


def symbol_name(symbol):
    return "Пробел" if symbol == " " else symbol


def save_csv(file_name, header, rows):
    path = BASE_DIR / file_name
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(header)
        writer.writerows(rows)


def format_weight(value):
    return f"{value:.3f}"


def create_table_1(text):
    total_symbols = len(text)
    freq = Counter(text)
    rows = []

    for symbol, count_value in sorted(freq.items(), key=lambda item: (-item[1], item[0])):
        rows.append(
            [
                symbol_name(symbol),
                count_value,
                total_symbols,
                f"{count_value / total_symbols:.3f}",
            ]
        )

    save_csv(
        "table_1_frequencies.csv",
        ["Символ", "Частота", "Всего символов", "Частость"],
        rows,
    )

    return total_symbols, freq


def build_huffman(freq):
    nodes = []
    for symbol, weight in sorted(freq.items(), key=lambda item: (-item[1], symbol_name(item[0]))):
        nodes.append(
            {
                "name": symbol_name(symbol),
                "symbol": symbol,
                "weight": weight,
                "left": None,
                "right": None,
            }
        )

    states = []
    merges = []
    step = 1

    while True:
        nodes.sort(key=lambda node: (-node["weight"], node["name"]))
        states.append([{"name": node["name"], "weight": node["weight"]} for node in nodes])

        if len(nodes) == 1:
            break

        node_2 = nodes.pop()
        node_1 = nodes.pop()

        new_node = {
            "name": f"U{step}",
            "symbol": None,
            "weight": node_1["weight"] + node_2["weight"],
            "left": node_1,
            "right": node_2,
        }

        merges.append(
            {
                "step": step,
                "left_name": node_1["name"],
                "left_weight": node_1["weight"],
                "right_name": node_2["name"],
                "right_weight": node_2["weight"],
                "new_name": new_node["name"],
                "new_weight": new_node["weight"],
            }
        )

        nodes.append(new_node)
        step += 1

    return nodes[0], states, merges


def create_table_2(states, merges, total_symbols):
    max_rows = len(states[0])
    html = [
        "<html><head><meta charset='utf-8'><style>",
        "body{margin:12px;background:white;}",
        "table{border-collapse:collapse;}",
        "td{border:1px solid #cfcfcf;min-width:58px;height:28px;text-align:center;padding:4px;font-family:Arial,sans-serif;font-size:14px;}",
        ".selected{background:#ffe699;}",
        ".new{background:#c6e0b4;}",
        "</style></head><body><table>",
    ]

    for row_index in range(max_rows):
        html.append("<tr>")
        for column_index, state in enumerate(states):
            if row_index >= len(state):
                html.append("<td></td>")
                continue

            item = state[row_index]
            value = format_weight(item["weight"] / total_symbols)

            cell_class = ""
            if column_index < len(merges) and row_index in (len(state) - 2, len(state) - 1):
                cell_class = "selected"
            if column_index > 0 and item["name"] == merges[column_index - 1]["new_name"]:
                cell_class = "new"

            if cell_class:
                html.append(f"<td class='{cell_class}'>{escape(value)}</td>")
            else:
                html.append(f"<td>{escape(value)}</td>")

        html.append("</tr>")

    html.append("</table></body></html>")
    (BASE_DIR / "table_2_huffman_steps.html").write_text("".join(html), encoding="utf-8")


def create_table_3(rows):
    csv_rows = []
    for symbol, frequency_value, code in rows:
        csv_rows.append([symbol, frequency_value, f'="{code}"'])

    save_csv(
        "table_3_codes.csv",
        ["Символ", "Частость", "Код"],
        csv_rows,
    )


def fill_codes(node, prefix, codes):
    if node["symbol"] is not None:
        codes[node["symbol"]] = prefix or "0"
        return

    fill_codes(node["left"], prefix + "0", codes)
    fill_codes(node["right"], prefix + "1", codes)


def tree_node_text(node, total_symbols):
    value = format_weight(node["weight"] / total_symbols)
    if node["symbol"] is None:
        return value
    return f"{symbol_name(node['symbol'])} ({value})"


def build_tree_lines(node, total_symbols, prefix=""):
    lines = []
    children = []

    if node["left"] is not None:
        children.append(("0", node["left"]))
    if node["right"] is not None:
        children.append(("1", node["right"]))

    for index, (bit, child) in enumerate(children):
        is_last = index == len(children) - 1
        connector = "└" if is_last else "├"
        lines.append(f"{prefix}{connector}─{bit}─► {tree_node_text(child, total_symbols)}")
        next_prefix = prefix + ("   " if is_last else "│  ")
        lines.extend(build_tree_lines(child, total_symbols, next_prefix))

    return lines


def create_tree_html(node, total_symbols):
    lines = [f"▲ {tree_node_text(node, total_symbols)}"]
    lines.extend(build_tree_lines(node, total_symbols))

    html = [
        "<html><head><meta charset='utf-8'><style>",
        "body{margin:12px;background:white;font-family:monospace;}",
        "pre{font-size:16px;line-height:1.5;}",
        "</style></head><body><pre>",
        escape("\n".join(lines)),
        "</pre></body></html>",
    ]

    (BASE_DIR / "huffman_tree.html").write_text("".join(html), encoding="utf-8")


def main():
    text = TEXT
    total_symbols, freq = create_table_1(text)

    tree, states, merges = build_huffman(freq)
    create_table_2(states, merges, total_symbols)

    codes = {}
    fill_codes(tree, "", codes)

    code_rows = []
    average_length = 0

    for symbol, count_value in sorted(freq.items(), key=lambda item: (-item[1], item[0])):
        probability = count_value / total_symbols
        code = codes[symbol]
        average_length += probability * len(code)
        code_rows.append([symbol_name(symbol), format_weight(probability), code])

    create_table_3(code_rows)

    log_value = log2(len(freq))
    fixed_code_length = ceil(log2(len(freq)))
    delta = fixed_code_length - average_length

    metrics_text = [
        f"Всего символов N = {total_symbols}",
        f"Количество используемых символов = {len(freq)}",
        f"Средняя длина кода Хаффмана = {average_length:.3f}",
        f"log2({len(freq)}) = {log_value:.3f}, значит длина фиксированного двоичного кода = {fixed_code_length}",
        f"Избыточность = {fixed_code_length} - {average_length:.3f} = {delta:.3f}",
    ]

    for line in metrics_text:
        print(line)

    create_tree_html(tree, total_symbols)


if __name__ == "__main__":
    main()
