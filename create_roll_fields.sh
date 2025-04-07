#!/bin/bash

# Insert the roll-specific fields into create.html
sed -i '83a\
            <!-- Roll Paper Specific Fields -->\
            <div class="roll-specific-fields mb-3" style="display: none;">\
                <div class="card">\
                    <div class="card-header bg-light">\
                        <h5 class="mb-0">Roll Paper Specific Details</h5>\
                    </div>\
                    <div class="card-body">\
                        <div class="mb-3">\
                            <div class="form-check">\
                                <input class="form-check-input" type="checkbox" id="is_roll" name="is_roll" value="1">\
                                <label class="form-check-label" for="is_roll">\
                                    This is roll media\
                                </label>\
                            </div>\
                            <div class="form-text">Check this if this paper comes on a roll</div>\
                        </div>\
                        <div class="mb-3">\
                            <label for="roll_length" class="form-label">Roll Length (feet)</label>\
                            <input type="number" name="roll_length" id="roll_length" class="form-control" step="0.1" min="0" placeholder="e.g., 150">\
                            <div class="form-text">The total length of the roll in feet</div>\
                        </div>\
                    </div>\
                </div>\
            </div>' templates/paper_options/create.html

# Insert the roll-specific fields into edit.html
sed -i '83a\
            <!-- Roll Paper Specific Fields -->\
            <div class="roll-specific-fields mb-3" {% if paper_option.size != "Roll" %}style="display: none;"{% endif %}>\
                <div class="card">\
                    <div class="card-header bg-light">\
                        <h5 class="mb-0">Roll Paper Specific Details</h5>\
                    </div>\
                    <div class="card-body">\
                        <div class="mb-3">\
                            <div class="form-check">\
                                <input class="form-check-input" type="checkbox" id="is_roll" name="is_roll" value="1" {% if paper_option.is_roll %}checked{% endif %}>\
                                <label class="form-check-label" for="is_roll">\
                                    This is roll media\
                                </label>\
                            </div>\
                            <div class="form-text">Check this if this paper comes on a roll</div>\
                        </div>\
                        <div class="mb-3">\
                            <label for="roll_length" class="form-label">Roll Length (feet)</label>\
                            <input type="number" name="roll_length" id="roll_length" class="form-control" step="0.1" min="0" value="{{ paper_option.roll_length or "" }}" placeholder="e.g., 150">\
                            <div class="form-text">The total length of the roll in feet</div>\
                        </div>\
                    </div>\
                </div>\
            </div>' templates/paper_options/edit.html
