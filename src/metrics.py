

import sys
import time
from enum import Enum

from typing import Final, TextIO


class ExitStatus(Enum) :
	SUCCESS = 0
	ERROR   = 1


class PatchType(Enum) :
	CONVERT = 0
	COPY    = 1
	MKDIR   = 2
	REMOVE  = 3


class MetadataCounters :

	def __init__(self, *args) :
		self.counters: dict[str,int] = { mdata: 0 for mdata in args }
	
	def incr(self, mdata: str) :
		if mdata in self.counters :
			self.counters[mdata] += 1
		else :
			self.counters[mdata] = 1


class ConversionMetrics :

	def __init__(self) :
		self.status = ExitStatus.SUCCESS
		self.start_time_sec: Final[float] = time.time()
		self.input_files = MetadataCounters('mp3', 'flac', 'm4a')
		self.output_files = MetadataCounters('mp3')
		self.convert_tags = MetadataCounters('always', 'bonus', 'skip')
		self.patches = MetadataCounters('convert', 'copy', 'mkdir', 'remove')
		self.ignored_files = MetadataCounters('mp3', 'flac', 'm4a')
		self._end_time_sec = 0.0
	
	def end(self) -> "ConversionMetrics" :
		self._end_time_sec = time.time()
		return self
	
	def get_duration(self) -> float :
		return self._end_time_sec - self.start_time_sec
	
	def summary(self) :
		print(f"Processed {sum(self.input_files.counters.values())} files from input directory")
		for ext, count in self.input_files.counters.items() :
			if count > 0 :
				print(f"  - {count} {ext}")
		print(f"Found {sum(self.output_files.counters.values())} files in destination directory")
		print(f"Performed {self.patches.counters['convert']} conversions, {self.patches.counters['copy']} copies and {self.patches.counters['remove']} removals in {int(self.get_duration() * 1000)}ms")
		print(f"Ignored {sum(self.ignored_files.counters.values())} files")
		print('Done' if self.status == ExitStatus.SUCCESS else 'Error')

	def print(self, out: TextIO = sys.stdout) :
		print('# TYPE mp3conv_exit_status counter',                                                          file = out)
		print('# HELP mp3conv_exit_status Status of the last run (0=OK, 1=ERROR).',                          file = out)
		print(f"mp3conv_exit_status {self.status.value}",                                                    file = out)

		print('# TYPE mp3conv_start_time counter',                                                           file = out)
		print('# HELP mp3conv_start_time Timestamp of the last run of the converter.',                       file = out)
		print(f"mp3conv_start_time {self.start_time_sec}",                                                   file = out)

		print('# TYPE mp3conv_run_time gauge',                                                               file = out)
		print('# HELP mp3conv_run_time Total run time of the conversion.',                                   file = out)
		print(f"mp3conv_run_time {self.get_duration()}",                                                     file = out)

		print('# TYPE mp3conv_input_files_count gauge',                                                      file = out)
		print('# HELP mp3conv_input_files_count Count of files in the input directory.',                     file = out)
		for ext, count in self.input_files.counters.items() :
			print(f"mp3conv_input_files_count{{extension=\"{ext}\"}} {count}",                               file = out)

		print('# TYPE mp3conv_output_files_count gauge',                                                     file = out)
		print('# HELP mp3conv_output_files_count Count of files in the output directory before conversion.', file = out)
		for ext, count in self.output_files.counters.items() :
			print(f"mp3conv_output_files_count{{extension=\"{ext}\"}} {count}",                              file = out)

		print('# TYPE mp3conv_convert_tags gauge',                                                           file = out)
		print('# HELP mp3conv_convert_tags Count of conversion tags found in input files.',                  file = out)
		for tag, count in self.convert_tags.counters.items() :
			print(f"mp3conv_convert_tags{{convert_tag=\"{tag}\"}} {count}",                                  file = out)

		print('# TYPE mp3conv_ignored_files_count gauge',                                                    file = out)
		print('# HELP mp3conv_ignored_files_count Number of files ignored by the script.',                   file = out)
		for ext, count in self.ignored_files.counters.items() :
			print(f"mp3conv_ignored_files_count{{extension=\"{ext}\"}} {count}",                             file = out)

		print('# TYPE mp3conv_patches_count gauge',                                                          file = out)
		print('# HELP mp3conv_patches_count Count of patches applied by the script.',                        file = out)
		for patch_type, count in self.patches.counters.items() :
			print(f"mp3conv_patches_count{{pach_type=\"{patch_type}\"}} {count}",                            file = out)

		
		


