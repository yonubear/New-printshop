#!/bin/bash

# Update the size column to show roll information
sed -i 's/<td>{{ option.size }}<\/td>/<td>\n                                {{ option.size }}\n                                {% if option.is_roll %}\n                                <span class="badge bg-info">Roll<\/span>\n                                {% endif %}\n                            <\/td>/g' templates/paper_options/index.html

# Add dimensions column information after size
sed -i '/<th>Size<\/th>/a \                        <th>Dimensions</th>' templates/paper_options/index.html

# Add dimensions information to the data table
sed -i '/<td>\n                                {{ option.size }}/a \                            <td>\n                                {% if option.width and option.height %}\n                                    {{ option.width }}" × {{ option.height }}"\n                                {% elif option.is_roll and option.width and option.roll_length %}\n                                    {{ option.width }}" × {{ option.roll_length }}ft\n                                {% else %}\n                                    --\n                                {% endif %}\n                            </td>' templates/paper_options/index.html

# Update the colspan for the "No paper options defined" message
sed -i 's/<td colspan="9"/<td colspan="10"/g' templates/paper_options/index.html
