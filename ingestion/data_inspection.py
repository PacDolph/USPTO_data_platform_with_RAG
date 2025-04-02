from lxml import etree as et
from collections import Counter

xml_file = r"F:\Chrome Download\ipg250318\ipg250318.xml"

with open(xml_file, "r", encoding="utf-8") as file:
    buffer = []
    in_block = False
    for line in file:
        if "<?xml" in line:
            if in_block:
                break
            else:
                buffer.append(line)
                in_block=True
        else:
            buffer.append(line)
    xml = "".join(buffer)
    # print(xml)

root = et.fromstring(xml.encode("utf-8"))
et.indent(root, space="  ")
print(et.tostring(root).decode("utf-8"))
tag_count = Counter(elem.tag for elem in root.iter())
# print(tag_count)
for tag, count in tag_count.most_common():
    print(f"tag: {tag}, count: {count}")
# unique_tags = {}
# context = et.iterparse(xml_file, events=("start","end"))
# for event, elem in context:
#     tag = elem.tag
#     if tag in unique_tags:
#         unique_tags[tag] += 1
#     else:
#         unique_tags[tag] = 1
#     elem.clear()

# for tag, count in unique_tags:
#     print(f"tag: {tag}, count: {count}")