TEMPLATE_FILE := $(CURRENT_DIR)/systemd/embybot.service
TARGET_FILE := /etc/systemd/system/embybot.service

.PHONY: install uninstall

install:
        pip install -r requirements.txt
        sed 's#{work_dir}#$(CURRENT_DIR)#g' $(TEMPLATE_FILE) > $(TARGET_FILE)
        systemctl daemon-reload
        systemctl enable --now embybot.service
        systemctl status embybot.service

uninstall:
        systemctl disable --now embybot.service
        rm -f $(TARGET_FILE)
        systemctl daemon-reload
        # pip uninstall -r requirements.txt"
