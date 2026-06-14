app_name = "tmj"
app_title = "Hicom System"
app_publisher = "Hicom System"
app_description = "Hicom System"
app_email = "h1com.syst3m@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "hicom16",
# 		"logo": "/assets/tmj/logo.png",
# 		"title": "Hicom System",
# 		"route": "/hicom16",
# 		"has_permission": "hicom16.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = ["/assets/tmj/css/custom.css"]
app_include_js = ["/assets/tmj/js/desk_overrides.js"]

# include js, css files in header of web template
web_include_css = ["/assets/tmj/css/custom.css"]
# web_include_js = "/assets/tmj/js/hicom16.js"

# Relabel app titles in the desk workspace sidebar (e.g. "ERPNext" -> "Hicom System")
extend_bootinfo = "tmj.boot.boot_session"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "hicom16/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "hicom16/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "hicom16.utils.jinja_methods",
# 	"filters": "hicom16.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "hicom16.install.before_install"
# after_install = "hicom16.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "hicom16.uninstall.before_uninstall"
# after_uninstall = "hicom16.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "hicom16.utils.before_app_install"
# after_app_install = "hicom16.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "hicom16.utils.before_app_uninstall"
# after_app_uninstall = "hicom16.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "hicom16.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "hicom16.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"hicom16.tasks.all"
# 	],
# 	"daily": [
# 		"hicom16.tasks.daily"
# 	],
# 	"hourly": [
# 		"hicom16.tasks.hourly"
# 	],
# 	"weekly": [
# 		"hicom16.tasks.weekly"
# 	],
# 	"monthly": [
# 		"hicom16.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "hicom16.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "hicom16.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "hicom16.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "hicom16.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["hicom16.utils.before_request"]
# after_request = ["hicom16.utils.after_request"]

# Job Events
# ----------
# before_job = ["hicom16.utils.before_job"]
# after_job = ["hicom16.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"hicom16.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

