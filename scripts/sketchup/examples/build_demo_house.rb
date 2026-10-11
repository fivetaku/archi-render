# archi-render 데모: 2층 박공지붕 주택을 만들고 클레이 스타일로 씬 2개를 export_scenes.rb로 내보낸다.
LOG = '/tmp/sketchup-demo/build.log'
def log(m); File.open(LOG, 'a') { |f| f.puts("#{Time.now.strftime('%H:%M:%S')} #{m}") }; end
log 'start'
UI.start_timer(2, true) do
  c = '/tmp/sketchup-demo/cmd.rb'
  if File.exist?(c)
    code = File.read(c); File.delete(c)
    begin; eval(code, TOPLEVEL_BINDING); log 'cmd ok'; rescue Exception => e; log "cmd ERROR #{e.class}: #{e.message}"; end
  end
end
UI.start_timer(8, false) do
  begin
    model = Sketchup.active_model
    model.start_operation('archi demo', true)
    ents = model.active_entities
    ents.clear!
    m = 1000.mm / 1000.0 # 1 m in inches
    w = 10 * m; d = 8 * m; h1 = 3.2 * m; h2 = 6.4 * m; ridge = 9.0 * m
    # 본체 매스
    base = ents.add_face([0,0,0],[w,0,0],[w,d,0],[0,d,0])
    base.reverse! if base.normal.z < 0
    base.pushpull(h2)
    # 박공지붕 (x 방향 용마루)
    tri = ents.add_face([0,0,h2],[0,d/2.0,ridge],[0,d,h2])
    tri.pushpull(tri.normal.x < 0 ? -w : w) rescue tri.pushpull(-w)
    # 앞면(y=0)에 창·문 개구부: 얕게 들어간 면
    openings = [
      [1.0*m, 0.0, 1.4*m, 2.4*m],   # 출입문
      [3.2*m, 0.9*m, 2.4*m, 1.6*m], # 1층 창
      [6.6*m, 0.9*m, 2.4*m, 1.6*m],
      [1.0*m, 4.1*m, 2.0*m, 1.4*m], # 2층 창
      [4.0*m, 4.1*m, 2.0*m, 1.4*m],
      [7.0*m, 4.1*m, 2.0*m, 1.4*m]
    ]
    openings.each do |x, z, ow, oh|
      f = ents.add_face([x,0,z],[x+ow,0,z],[x+ow,0,z+oh],[x,0,z+oh])
      f.pushpull(-0.25*m) if f
    end
    # 옆면(x=w) 창 2개
    [[2.0*m, 1.0*m], [2.0*m, 4.2*m]].each do |y, z|
      f = ents.add_face([w,y,z],[w,y+1.8*m,z],[w,y+1.8*m,z+1.4*m],[w,y,z+1.4*m])
      f.pushpull(-0.25*m) if f
    end
    # 앞마당 데크
    deck = ents.add_face([-1*m,-3*m,0],[w+1*m,-3*m,0],[w+1*m,0,0],[-1*m,0,0])
    deck.reverse! if deck.normal.z < 0
    deck.pushpull(0.15*m)
    # 클레이: 모든 면을 흰 재질
    white = model.materials.add('clay_white'); white.color = Sketchup::Color.new(245,245,245)
    ents.grep(Sketchup::Face).each { |f| f.material = white; f.back_material = white }
    ro = model.rendering_options
    { 'RenderMode' => 2, 'Texture' => false, 'DrawHorizon' => false, 'DrawGround' => false,
      'DrawSky' => false, 'BackgroundColor' => Sketchup::Color.new(255,255,255) }.each do |k, v|
      begin; ro[k] = v; rescue StandardError => e; log "skip ro #{k}: #{e.message}"; end
    end
    si = model.shadow_info
    si['DisplayShadows'] = true
    si['UseSunForAllShading'] = true
    si['ShadowTime'] = Time.utc(2026, 10, 11, 15, 0, 0)
    model.commit_operation
    view = model.active_view
    pages = model.pages
    pages.to_a.each { |p| pages.erase(p) }
    cams = {
      'S01_entrance' => [[-9*m, -16*m, 1.6*m], [w/2.0, d/2.0, 3.5*m]],
      'S02_corner'   => [[w+12*m, -12*m, 1.6*m], [w/2.0, d/2.0, 3.5*m]]
    }
    cams.each do |name, (eye, tgt)|
      view.camera = Sketchup::Camera.new(eye, tgt, [0,0,1], true, 40)
      pg = pages.add(name)
      pg.use_camera = true; pg.use_shadow_info = true; pg.use_rendering_options = true
    end
    dir = File.join(Dir.home, 'Desktop', 'archi-demo')
    Dir.mkdir(dir) unless File.exist?(dir)
    model.save(File.join(dir, 'archi-demo-house.skp'))
    log "built; RenderMode=#{ro['RenderMode']} shadows=#{si['DisplayShadows']} pages=#{pages.count}"
    load '/Users/chulrolee/archi-render/scripts/sketchup/export_scenes.rb'
    log 'export done'
  rescue Exception => e
    Sketchup.active_model.abort_operation rescue nil
    log "ERROR #{e.class}: #{e.message}\n#{e.backtrace.first(5).join("\n")}"
  end
end
