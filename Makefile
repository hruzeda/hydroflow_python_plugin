#/***************************************************************************
# Hydroflow
#
# Compute drainage orders in drainage basins using Strahler and Shreve methods
#							 -------------------
#		begin				: 2024-08-07
#		git sha				: $Format:%H$
#		copyright			: (C) 2024 by Henrique Uzêda
#		email				: hruzeda@gmail.com
# ***************************************************************************/
#
#/***************************************************************************
# *																		 *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or	 *
# *   (at your option) any later version.								   *
# *																		 *
# ***************************************************************************/

#################################################
# Edit the following to match your sources lists
#################################################

LOCALES =

SOURCES = __init__.py classificator.py controller.py frmlog_ui.py frmlog.py hydroflow_dialog_base_ui.py hydroflow_dialog.py hydroflow.py params.py plugin_upload.py resources_rc.py models/__init__.py models/attribute.py models/feature_set.py models/feature.py models/new_feature_attribute.py models/node.py models/observation.py models/position.py models/relation.py models/segment.py models/vertex.py utils/__init__.py utils/geometry.py utils/iterator.py utils/message.py utils/shp_feature_set_dao.py

PLUGINNAME = hydroflow

PY_FILES = __init__.py classificator.py controller.py frmlog_ui.py frmlog.py hydroflow_dialog_base_ui.py hydroflow_dialog.py hydroflow.py params.py plugin_upload.py resources_rc.py

UI_FILES = frmlog.ui hydroflow_dialog_base.ui

EXTRAS = metadata.txt hydroflow.ico hydroflow.png search.ico

EXTRA_DIRS = models utils

COMPILED_RESOURCE_FILES = resources_rc.py

PEP8EXCLUDE=pydev,resources_rc.py,conf.py,third_party,ui

# QGISDIR points to the location where your plugin should be installed.
# This varies by platform, relative to your HOME directory:
#	* Linux:
#	  .local/share/QGIS/QGIS3/profiles/default/python/plugins/
#	* Mac OS X:
#	  Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins
#	* Windows:
#	  AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins'

QGISDIR=C:/Users/henrique/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins

#################################################
# Normally you would not need to edit below here
#################################################

HELP = help/build/html

PLUGIN_UPLOAD = ./plugin_upload.py

.PHONY: default
default:
	@echo While you can use make to build and deploy your plugin, pb_tool
	@echo is a much better solution.
	@echo A Python script, pb_tool provides platform independent management of
	@echo your plugins and runs anywhere.
	@echo You can install pb_tool using: pip install pb_tool
	@echo See https://g-sherman.github.io/plugin_build_tool/ for info.

compile: $(COMPILED_RESOURCE_FILES)
	@echo
	@echo "------------------------------------"
	@echo "Compiling UI and resource files"
	@echo "------------------------------------"
	python -m pyqt5ac --config pyqt5ac.config.yml

test: compile
	@echo
	@echo "----------------------"
	@echo "Regression Test Suite"
	@echo "----------------------"

	@# Preceding dash means that make will continue in case of errors
	@-export QGIS_DEBUG=0; \
		export QGIS_LOG_FILE=/dev/null; \
		nosetests -v --with-id --with-coverage --cover-package=. \
		3>&1 1>&2 2>&3 3>&- || true
	@echo "----------------------"
	@echo "If you get a 'no module named qgis.core error, try sourcing"
	@echo "the helper script we have provided first then run make test."
	@echo "e.g. source run-env-linux.sh <path to qgis install>; make test"
	@echo "----------------------"

deploy: compile
	@echo
	@echo "------------------------------------------"
	@echo "Deploying plugin to your .qgis2 directory."
	@echo "------------------------------------------"
	# The deploy  target only works on unix like operating system where
	# the Python plugin directory is located at:
	# $(QGISDIR)
	rm -rf $(QGISDIR)/$(PLUGINNAME)
	mkdir $(QGISDIR)/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(QGISDIR)/$(PLUGINNAME)
	cp -vf $(UI_FILES) $(QGISDIR)/$(PLUGINNAME)
	cp -vf $(COMPILED_RESOURCE_FILES) $(QGISDIR)/$(PLUGINNAME)
	cp -vf $(EXTRAS) $(QGISDIR)/$(PLUGINNAME)
	cp -rvf ${EXTRA_DIRS} $(QGISDIR)/$(PLUGINNAME)

# The dclean target removes compiled python files from plugin directory
# also deletes any .git entry
dclean:
	@echo
	@echo "-----------------------------------"
	@echo "Removing any compiled python files."
	@echo "-----------------------------------"
	rm -rf "**\__pycache__"
	rm -rf "**\.pyc"


derase:
	@echo
	@echo "-------------------------"
	@echo "Removing deployed plugin."
	@echo "-------------------------"
	rm -Rf $(QGISDIR)/$(PLUGINNAME)

zip: dclean package
	@echo
	@if [ -n "$(VERSION)" ]; then \
		echo "---------------------------"; \
		echo "Creating plugin zip bundle."; \
		echo "---------------------------"; \
		echo "The zip target deploys the plugin and creates a zip file with the deployed"; \
		echo "content. You can then upload the zip file on http://plugins.qgis.org"; \
		rm -f $(PLUGINNAME)-$(VERSION).zip; \
		cd $(QGISDIR); zip -9r $(CURDIR)/$(PLUGINNAME)-$(VERSION).zip $(PLUGINNAME); \
	fi

package: compile
	@echo
	@echo "------------------------------------"
	@echo "Exporting plugin to zip package."
	@echo "------------------------------------"
	@if [ -n "$(VERSION)" ]; then \
		rm -f $(PLUGINNAME)-$(VERSION).zip; \
		git archive --format zip --prefix "$(PLUGINNAME)/" -o $(PLUGINNAME)-$(VERSION).zip; \
		echo "Created package: $(PLUGINNAME)-$(VERSION).zip"; \
	else \
		echo "Create a zip package of the plugin named $(PLUGINNAME)-$(VERSION).zip."; \
		echo "This requires use of git (your plugin development directory must be a"; \
		echo "git repository)."; \
		echo "To use, pass a valid commit or tag as follows:"; \
		echo "make package VERSION=Version_0.3.2"; \
		echo; \
		echo "ERROR: VERSION variable is not defined."; \
	fi

upload: zip
	@if [ -n "$(VERSION)" ]; then \
		echo; \
		echo "-------------------------------------"; \
		echo "Uploading plugin to QGIS Plugin repo."; \
		echo "-------------------------------------"; \
		echo; \
		python $(PLUGIN_UPLOAD) $(PLUGINNAME)-$(VERSION).zip; \
	fi

clean:
	@echo
	@echo "------------------------------------"
	@echo "Removing uic and rcc generated files"
	@echo "------------------------------------"
	rm $(COMPILED_UI_FILES) $(COMPILED_RESOURCE_FILES)

lint:
	@echo
	@echo "------------------------------------"
	@echo "Running ruff check command with --fix"
	@echo "------------------------------------"
	ruff check --fix --config pyproject.toml

	@echo
	@echo "------------------------------------"
	@echo "Running pylint"
	@echo "------------------------------------"
	pylint -rn -sn --ignore-paths test --ignore frmlog_ui.py,hydroflow_dialog_base_ui.py,hydroflow.py,plugin_upload.py,resources_rc.py **/*.py

	@echo
	@echo "------------------------------------"
	@echo "Running mypy"
	@echo "------------------------------------"
	mypy --config-file .\pyproject.toml .

format:
	@echo
	@echo "------------------------------------"
	@echo "Running ruff check isort with --fix"
	@echo "------------------------------------"
	ruff check --select I --fix --config pyproject.toml

	@echo
	@echo "------------------------------------"
	@echo "Running ruff format command"
	@echo "------------------------------------"
	ruff format --config pyproject.toml