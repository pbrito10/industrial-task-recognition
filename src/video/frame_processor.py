# Processa cada frame individualmente na pipeline principal.
#
# Responsabilidade: para um frame recebido, orquestrar a sequência:
#   deteção → classificação de zona → atualização do state machine
#
# Lógica (método process(frame) → FrameResult):
#   1. Chama detector.detect(frame) → list[HandDetection]
#      Cada HandDetection tem keypoints (KeypointCollection),
#      bounding_box (BoundingBox), confidence (Confidence)
#      e hand_side (HandSide)
#   2. Chama zone_classifier.classify(detections):
#      → recebe list[HandDetection]
#      → devolve list[(HandDetection, RegionOfInterest | None)]
#      → internamente usa bounding_box.center() → Point,
#        passando-o a roi_collection.find_zone_for_point(point: Point)
#   3. Chama state_machine.update(hand_zones):
#      → a máquina transita entre TaskState
#      → devolve TaskEvent | None se uma tarefa foi concluída ou
#        forçada por timeout (was_forced=True)
#   4. Gera ZoneEvents (ENTER/EXIT) com EventType, HandSide, Point,
#      Confidence e was_forced — sem primitivos soltos
#   5. Desenha no frame: ROIs, keypoints, bounding boxes e zona ativa
#   6. Devolve FrameResult(annotated_frame, zone_events, task_event)
#      em vez de tupla — ver video/frame_result.py
#
# Este ficheiro processa um único frame. O loop de frames fica em
# run_program.py (separação de responsabilidades).
