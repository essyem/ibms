from django.template.loaders.filesystem import Loader as FilesystemLoader
from django.contrib.sites.shortcuts import get_current_site
import os

class SiteTemplateLoader(FilesystemLoader):
    """
    A custom template loader that loads templates from site-specific directories.
    """
    def get_template_sources(self, template_name):
        template_dirs = self.get_dirs()
        
        # Get current site from thread local storage or fallback to default
        from django.conf import settings
        try:
            from threading import local
            _thread_locals = local()
            request = getattr(_thread_locals, 'request', None)
            if request:
                current_site = get_current_site(request)
                site_folder = f'sites/{current_site.domain.split(".")[0]}'
                site_template_dirs = [os.path.join(template_dir, site_folder) for template_dir in template_dirs]
                
                # First check site-specific templates
                for template_dir in site_template_dirs:
                    if os.path.isdir(template_dir):
                        yield from super().get_template_sources(template_name)
        except:
            # Fallback to default template loading if any issues
            pass
        
        # Then check default templates
        yield from super().get_template_sources(template_name)
