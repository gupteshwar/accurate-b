from .common_site_config import get_config
import re, os, subprocess, semantic_version
import bench

try:
	from urllib.parse import urlparse
except ImportError:
	from urlparse import urlparse

def generate_config(bench_path):
	config = get_config(bench_path)

	ports = {}
	for key in ('redis_cache', 'redis_queue', 'redis_socketio'):
		ports[key] = urlparse(config[key]).port

	write_redis_config(
		template_name='redis_queue.conf',
		context={
			"port": ports['redis_queue'],
			"bench_path": os.path.abspath(bench_path),
		},
		bench_path=bench_path
	)

	write_redis_config(
		template_name='redis_socketio.conf',
		context={
			"port": ports['redis_socketio'],
		},
		bench_path=bench_path
	)

	write_redis_config(
		template_name='redis_cache.conf',
		context={
			"maxmemory": config.get('cache_maxmemory', get_max_redis_memory()),
			"port": ports['redis_cache'],
			"redis_version": get_redis_version(),
		},
		bench_path=bench_path
	)

	# make pids folder
	pid_path = os.path.join(bench_path, "config", "pids")
	if not os.path.exists(pid_path):
		os.makedirs(pid_path)

def write_redis_config(template_name, context, bench_path):
	template = bench.env.get_template(template_name)

	if "pid_path" not in context:
		context["pid_path"] = os.path.abspath(os.path.join(bench_path, "config", "pids"))

	with open(os.path.join(bench_path, 'config', template_name), 'w') as f:
		f.write(template.render(**context))

def get_redis_version():
	version_string = subprocess.check_output('redis-server --version', shell=True).decode().strip()

	# extract version number from string
	version = re.findall("\d+\.\d+", version_string)
	if not version:
		return None

	version = semantic_version.Version(version[0], partial=True)
	return float('{major}.{minor}'.format(major=version.major, minor=version.minor))

def get_max_redis_memory():
	import psutil
	
	total_virtual_mem = psutil.virtual_memory().total/(pow(1024, 2))
	max_memory = int(total_virtual_mem * 0.05) # Max memory for redis is 5% of virtual memory

	if max_memory < 50:
		return 50
	else:
		return max_memory
