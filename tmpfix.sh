#!/bin/bash
# Add Roll Paper option to the size dropdown in create.html
sed -i '59i \                        <option value="Roll">Roll Paper</option>' templates/paper_options/create.html

# Add Roll Paper option to the size dropdown in edit.html
sed -i '59i \                        <option value="Roll" {% if paper_option.size == "Roll" %}selected{% endif %}>Roll Paper</option>' templates/paper_options/edit.html
