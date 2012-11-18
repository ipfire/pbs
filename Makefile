
PO_PATH = data/translations
POTFILE = $(PO_PATH)/pakfire.pot
POFILES = $(wildcard $(PO_PATH)/*/LC_MESSAGES/pakfire.po)

ALL_FILES = $(shell find . /usr/lib*/python*/site-packages/tornado -name "*.py" -or -name "*.html")

.PHONY: all
all: po

.PHONY: pot
pot: $(POTFILE)

$(POTFILE): $(ALL_FILES)
	xgettext --language=Python --from-code=UTF-8 --keyword=_:1,2 --keyword=N_ -d pakfire -o $(POTFILE) \
		$(ALL_FILES)

.PHONY: po
po: $(POTFILE) $(patsubst %.po, %.mo, $(POFILES))

# Merge the POTFILE.
%.po: $(POTFILE)
	msgmerge $@ $(POTFILE) -o $@

# Compile the translations.
%.mo: %.po
	msgfmt $< -o $@

.PHONY: po-update
po-update:
	tx pull --all
