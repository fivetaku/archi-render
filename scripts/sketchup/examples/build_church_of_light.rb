# build_church_of_light.rb — 안도 다다오 「빛의 교회」(1989) 학습용 매스 모델
#
# 치수 근거: 20-knowledge/references/church-of-light/FINDINGS.md §8 (도면 실측·공표 치수 종합, 일부 추정)
# 좌표: X = 본당 길이 방향(0 = 제단 쪽 남측 내벽, 17.7 = 북측 내벽), Y = 폭(0 = 동측 내벽, 5.9 = 서측 내벽), Z = 높이(0 = 뒤쪽 바닥)
# 실행: SketchUp Ruby 콘솔에서  load "/Users/chulrolee/archi-render/scripts/sketchup/examples/build_church_of_light.rb"
# 결과: 클레이(흰색) 모델 + 씬 3개(S01_exterior, S02_cross, S03_aerial) + ~/Desktop/archi-demo/church-of-light.skp
# 학습용 재현 모델이며 실제 도면과 다를 수 있다(벤치 개수·출입문 폭·일요학교 별동은 생략 또는 추정).

module ChurchOfLight
  M = 1000.mm / 1000.0          # 1 m (inch 단위)
  TIE_HOLES = true              # 노출콘크리트 패널 줄눈 + 폼타이 구멍 (1800×900, 3×2 @600×450)
  LOG = '/tmp/sketchup-demo/church.log'

  def self.log(msg)
    File.open(LOG, 'a') { |f| f.puts("#{Time.now.strftime('%H:%M:%S')} #{msg}") } rescue nil
    puts "[church] #{msg}"
  end

  def self.pt(x, y, z)
    Geom::Point3d.new(x * M, y * M, z * M)
  end

  # 축 정렬 박스 그룹
  def self.box(ents, name, x0, y0, z0, x1, y1, z1, mat)
    g = ents.add_group; g.name = name
    f = g.entities.add_face(pt(x0, y0, z0), pt(x1, y0, z0), pt(x1, y1, z0), pt(x0, y1, z0))
    f.reverse! if f.normal.z < 0
    f.pushpull((z1 - z0) * M)
    paint(g, mat); g
  end

  # 평면 위 선분(P1→P2)을 두께 t, 높이 z0~z1 로 세운 벽 그룹. 반환: [그룹, 바깥 법선(+n 쪽)]
  def self.slab_wall(ents, name, p1, p2, t, z0, z1, mat)
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    len = Math.sqrt(dx * dx + dy * dy); ux, uy = dx / len, dy / len
    nx, ny = -uy, ux
    h = t / 2.0
    a = [p1[0] - nx * h, p1[1] - ny * h]; b = [p2[0] - nx * h, p2[1] - ny * h]
    c = [p2[0] + nx * h, p2[1] + ny * h]; d = [p1[0] + nx * h, p1[1] + ny * h]
    g = ents.add_group; g.name = name
    f = g.entities.add_face(pt(a[0], a[1], z0), pt(b[0], b[1], z0), pt(c[0], c[1], z0), pt(d[0], d[1], z0))
    f.reverse! if f.normal.z < 0
    f.pushpull((z1 - z0) * M)
    paint(g, mat)
    [g, [nx, ny], [ux, uy], len]
  end

  def self.paint(g, mat)
    g.entities.grep(Sketchup::Face).each { |f| f.material = mat; f.back_material = mat }
  end

  # 수직면 위에 패널 줄눈과 폼타이 구멍을 새긴다.
  # o = 면 위 시작점(x,y), u = 면을 따라가는 단위벡터(x,y), n = 바깥 법선(x,y), len = 길이, z0~z1 = 높이
  def self.panelize(g, o, u, n, len, z0, z1)
    return unless TIE_HOLES
    ents = g.entities
    pw, ph = 1.8, 0.9
    normal = Geom::Vector3d.new(n[0], n[1], 0)
    at = ->(s, z) { pt(o[0] + u[0] * s, o[1] + u[1] * s, z) }
    # 세로 줄눈
    s = pw
    while s < len - 0.05
      ents.add_line(at.(s, z0), at.(s, z1)); s += pw
    end
    # 가로 줄눈
    z = z0 + ph
    while z < z1 - 0.05
      ents.add_line(at.(0, z), at.(len, z)); z += ph
    end
    # 구멍: 패널마다 3×2, @600×450 (패널 안 0.3/0.9/1.5, 0.225/0.675)
    holes = 0
    s0 = 0.0
    while s0 + pw <= len + 0.01
      zz = z0
      while zz + ph <= z1 + 0.01
        [0.3, 0.9, 1.5].each do |du|
          [0.225, 0.675].each do |dv|
            c = at.(s0 + du, zz + dv)
            edges = ents.add_circle(c, normal, 0.016 * M, 10)
            face = edges.first.faces.min_by(&:area) rescue nil
            if face && face.area < (0.05 * M)**2
              face.pushpull(-0.02 * M) rescue nil
              holes += 1
            end
          end
        end
        zz += ph
      end
      s0 += pw
    end
    holes
  end

  def self.build
    model = Sketchup.active_model
    model.start_operation('빛의 교회', true)
    ents = model.active_entities
    ents.clear!
    mats = model.materials
    clay = mats['col_clay'] || mats.add('col_clay'); clay.color = Sketchup::Color.new(244, 244, 242)
    glass = mats['col_glass'] || mats.add('col_glass'); glass.color = Sketchup::Color.new(200, 225, 235); glass.alpha = 0.25

    gl = -0.15                 # 바깥 지면
    zb = -1.10                 # 제단 바닥 = 벽 바닥
    ceil = 5.90; roof = 6.79

    # 지면
    ground = ents.add_group; ground.name = 'ground'
    gf = ground.entities.add_face(pt(-14, -12, gl), pt(32, -12, gl), pt(32, 22, gl), pt(-14, 22, gl))
    gf.reverse! if gf.normal.z < 0
    paint(ground, clay)

    # 측벽: 동측(Y -0.38~0) 통벽, 서측(Y 5.9~6.28) 유리 구간 X 3.49~14.41
    east = box(ents, 'wall_east', -0.25, -0.38, zb, 17.95, 0.0, ceil, clay)
    panelize(east, [-0.25, -0.38], [1, 0], [0, -1], 18.2, gl, ceil)
    w1 = box(ents, 'wall_west_s', -0.25, 5.90, zb, 3.49, 6.28, ceil, clay)
    w2 = box(ents, 'wall_west_n', 14.41, 5.90, zb, 17.95, 6.28, ceil, clay)
    box(ents, 'wall_west_base', 3.49, 5.90, zb, 14.41, 6.28, 0.0, clay)
    box(ents, 'wall_west_lintel', 3.49, 5.90, 5.55, 14.41, 6.28, ceil, clay)
    gw = box(ents, 'glass_west', 3.49, 6.07, 0.0, 14.41, 6.11, 5.55, glass)
    panelize(w2, [17.95, 6.28], [-1, 0], [0, 1], 3.54, gl, ceil)

    # 남측(제단) 벽 X -0.25~0, 십자 슬릿 폭 0.20: 세로 Y 2.85~3.05 전체 높이, 가로 Z 2.85~3.05 내부 전폭
    [[0.0, 2.85], [3.05, 5.90]].each do |y0, y1|
      [[zb, 2.85], [3.05, ceil]].each do |z0, z1|
        box(ents, 'wall_south', -0.25, y0, z0, 0.0, y1, z1, clay)
      end
    end
    # 북측 벽
    north = box(ents, 'wall_north', 17.70, 0.0, gl, 17.95, 5.90, ceil, clay)
    panelize(north, [17.95, 0.0], [0, 1], [1, 0], 5.9, gl, ceil)

    # 지붕(평지붕 + 파라펫 높이 포함 슬래브)
    box(ents, 'roof', -0.25, -0.38, ceil, 17.95, 6.28, roof, clay)

    # 바닥: 제단 X 0~3.45 Z -1.10 / 단 10개(깊이 0.90, 높이 0.10) / 뒤쪽 X 12.45~17.70 Z 0
    box(ents, 'floor_altar', 0.0, 0.0, zb - 0.2, 3.45, 5.90, zb, clay)
    10.times do |i|
      x0 = 3.45 + 0.90 * i; top = -1.00 + 0.10 * i
      box(ents, "tread_#{i + 1}", x0, 0.0, zb - 0.2, x0 + 0.90, 5.90, top, clay)
      # 나무 벤치(각 단 1줄, 좌판 깊이 0.37, 높이 0.42) — 도면 따라 Y 0.65~5.22
      box(ents, "bench_#{i + 1}", x0 + 0.42, 0.65, top, x0 + 0.79, 5.22, top + 0.42, clay)
    end
    box(ents, 'floor_rear', 12.45, 0.0, zb - 0.2, 17.70, 5.90, 0.0, clay)
    # 제단 탁자·강대
    box(ents, 'altar_table', 0.65, 4.85, zb, 2.45, 5.54, zb + 0.85, clay)
    box(ents, 'lectern', 1.64, 3.27, zb, 2.23, 4.18, zb + 1.05, clay)

    # 15° 사선 벽(두께 0.28, 상단 5.72 — 천장과 0.18 틈): 장벽 + 출입 틈 1.6 + 북측 벽 관통 단벽
    line = ->(x) { 9.15 - (x + 2.03) * Math.tan(15 * Math::PI / 180) }
    g, n, u, len = slab_wall(ents, 'wall_15deg_long', [-2.03, 9.15], [14.98, line.(14.98)], 0.28, zb, 5.72, clay)
    panelize(g, [-2.03 + n[0] * 0.14, 9.15 + n[1] * 0.14], u, n, len, gl, 5.72)
    slab_wall(ents, 'wall_15deg_short', [16.52, line.(16.52)], [18.97, line.(18.97)], 0.28, zb, 5.72, clay)
    # 리턴 벽(사선 벽 시작점에서 남쪽으로)
    rw = box(ents, 'wall_return', -2.03, 5.19, gl, -1.75, 9.15, gl + 5.87, clay)
    # 바깥 계단(남서측, 제단 레벨로)
    4.times { |i| box(ents, "ext_step_#{i + 1}", -1.75, 0.43 + 0.39 * i, zb, -0.25, 0.43 + 0.39 * (i + 1), gl - 0.24 * (3 - i), clay) }

    # 스타일: 흰 배경·지평선 끔·그림자 켬, 이바라키 위치
    ro = model.rendering_options
    { 'RenderMode' => 2, 'DrawHorizon' => false, 'DrawGround' => false, 'DisplayWatermarks' => false,
      'DisplayFog' => false, 'BackgroundColor' => Sketchup::Color.new(255, 255, 255) }.each { |k, v| (ro[k] = v) rescue nil }
    si = model.shadow_info
    { 'Latitude' => 34.83, 'Longitude' => 135.56, 'TZOffset' => 9.0, 'City' => 'Ibaraki',
      'Country' => 'Japan', 'NorthAngle' => 25.0, 'DisplayShadows' => true, 'UseSunForAllShading' => true }.each { |k, v| (si[k] = v) rescue nil }
    si['ShadowTime'] = Time.utc(2026, 10, 11, 1, 30, 0)   # 현지 10:30
    model.styles.update_selected_style rescue nil
    model.commit_operation
    log "built: groups=#{ents.grep(Sketchup::Group).size} sun=#{si['SunDirection'].to_a.map { |v| v.round(2) }}"
    scenes(model)
  end

  def self.scenes(model)
    view = model.active_view
    pages = model.pages
    pages.to_a.each { |p| pages.erase(p) }
    begin; model.options['PageOptions']['ShowTransition'] = false; rescue StandardError; end
    cams = {
      'S01_exterior' => [[28.0, 17.0, 1.6], [7.5, 5.0, 2.6], 40],   # 북서쪽, 사선 벽과 박스
      'S02_cross'    => [[17.2, 2.95, 1.6], [0.0, 2.95, 1.9], 62],  # 뒤쪽 바닥에서 제단 십자 보기
      'S03_aerial'   => [[30.0, 22.0, 24.0], [8.0, 4.0, 0.0], 35]   # 조감
    }
    cams.each do |name, (eye, tgt, fov)|
      view.camera = Sketchup::Camera.new(pt(*eye), pt(*tgt), Geom::Vector3d.new(0, 0, 1), true, fov)
      pg = pages.add(name)
      pg.use_camera = true; pg.use_shadow_info = true; pg.use_rendering_options = true; pg.use_style = true
    end
    pages.selected_page = pages['S01_exterior']
    dir = File.join(Dir.home, 'Desktop', 'archi-demo'); Dir.mkdir(dir) unless File.exist?(dir)
    model.save(File.join(dir, 'church-of-light.skp'))
    log "scenes=#{pages.count} saved=#{model.path}"
  end
end

ChurchOfLight.build
