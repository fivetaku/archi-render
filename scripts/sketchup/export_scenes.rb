# export_scenes.rb — SketchUp scene exporter for archi-render (runs on the user's SketchUp PC, not on the Mac).
#
# For every scene (model.pages) it writes a 2000px-wide PNG (height keeps the viewport aspect)
# plus camera.json, into  ~/Desktop/archi-render-export/<model-name>/<scene-name>/
#   capture.png   — the render source. Set the scene style to a clay/monochrome style + shadows first
#                   (design P6: no native depth map, so the capture must carry clear face shading).
#   camera.json   — eye/target/up/fov/perspective/aspect for reproducibility.
# Copy the folder into the workspace and run /intake (or render.py --input ...).
#
# HOW TO RUN
#   A) Ruby Console: Window ▸ Ruby Console ▸  load "C:/path/to/export_scenes.rb"
#   B) Startup:      sketchup.exe -RubyStartup "C:/path/to/export_scenes.rb"  (opens the model, then exports)
#   C) Plugins dir:  drop into Plugins/ and it exports at every launch — not recommended.
# Options: change WIDTH / OUT_ROOT below. Scene names are sanitised for filesystem use.
# SketchUp 2025/2026 tested API surface only: Sketchup.active_model, Model#pages, Pages#selected_page=,
# View#write_image (hash form), Camera. 2026.2 raises LoadError/RuntimeError on some `require`
# paths, so everything is wrapped in begin/rescue and one failing scene does not abort the batch.

require 'json'
require 'fileutils'

module ArchiRenderExport
  WIDTH    = 2000
  OUT_ROOT = File.join(Dir.home, 'Desktop', 'archi-render-export')

  def self.sanitize(name)
    s = name.to_s.strip.gsub(/[^\w\-. ]+/, '_').gsub(/\s+/, '_')
    s.empty? ? 'scene' : s
  end

  def self.camera_hash(camera, aspect)
    {
      'eye'         => camera.eye.to_a.map { |v| v.to_f },
      'target'      => camera.target.to_a.map { |v| v.to_f },
      'up'          => camera.up.to_a.map { |v| v.to_f },
      'perspective' => camera.perspective?,
      'fov_deg'     => (camera.perspective? ? camera.fov.to_f : nil),
      'height_in'   => (camera.perspective? ? nil : camera.height.to_f),
      'aspect'      => aspect,
      'units'       => 'inches'
    }
  end

  def self.run
    model = Sketchup.active_model
    raise 'No active model' unless model
    view  = model.active_view
    model_name = sanitize(model.title.to_s.empty? ? 'untitled' : model.title)
    pages = model.pages
    if pages.count == 0
      puts '[archi-render] model has no scenes — create scenes (View ▸ Animation ▸ Add Scene) and lock the camera.'
      return
    end

    aspect = view.vpwidth.to_f / view.vpheight.to_f
    height = (WIDTH / aspect).round
    ok = 0
    pages.each do |page|
      scene = sanitize(page.name)
      dir   = File.join(OUT_ROOT, model_name, scene)
      begin
        FileUtils.mkdir_p(dir)
        pages.selected_page = page          # applies camera, style, shadows of that scene
        view.refresh
        png = File.join(dir, 'capture.png')
        view.write_image(filename: png, width: WIDTH, height: height, antialias: true, transparent: false)
        cam = page.camera || view.camera
        File.write(File.join(dir, 'camera.json'),
                   JSON.pretty_generate(camera_hash(cam, aspect).merge('scene' => page.name,
                                                                        'model' => model_name,
                                                                        'width' => WIDTH, 'height' => height)))
        ok += 1
        puts "[archi-render] #{scene} → #{png} (#{WIDTH}x#{height})"
      rescue LoadError, StandardError => e
        puts "[archi-render] FAILED #{scene}: #{e.class}: #{e.message}"
      end
    end
    puts "[archi-render] done: #{ok}/#{pages.count} scenes → #{File.join(OUT_ROOT, model_name)}"
  end
end

begin
  ArchiRenderExport.run
rescue LoadError, StandardError => e
  puts "[archi-render] export aborted: #{e.class}: #{e.message}"
end
