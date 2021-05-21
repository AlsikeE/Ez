# Details

Date : 2021-05-15 20:57:49

Directory /root/ez-segway

Total : 97 files,  11634 codes, 1815 comments, 2284 blanks, all 15733 lines

[summary](results.md)

## Files
| filename | language | code | comment | blank | total |
| :--- | :--- | ---: | ---: | ---: | ---: |
| [__init__.py](/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [simulator/__init__.py](/simulator/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [simulator/analytic.py](/simulator/analytic.py) | Python | 39 | 5 | 8 | 52 |
| [simulator/convert_flows.py](/simulator/convert_flows.py) | Python | 35 | 0 | 7 | 42 |
| [simulator/datasender.py](/simulator/datasender.py) | Python | 95 | 7 | 21 | 123 |
| [simulator/devices/__init__.py](/simulator/devices/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [simulator/devices/centralized_controller.py](/simulator/devices/centralized_controller.py) | Python | 33 | 2 | 6 | 41 |
| [simulator/devices/centralized_switch.py](/simulator/devices/centralized_switch.py) | Python | 25 | 0 | 5 | 30 |
| [simulator/devices/controller.py](/simulator/devices/controller.py) | Python | 53 | 2 | 18 | 73 |
| [simulator/devices/ez_segway_controller.py](/simulator/devices/ez_segway_controller.py) | Python | 12 | 0 | 5 | 17 |
| [simulator/devices/ez_segway_switch.py](/simulator/devices/ez_segway_switch.py) | Python | 24 | 2 | 7 | 33 |
| [simulator/devices/switch.py](/simulator/devices/switch.py) | Python | 75 | 2 | 24 | 101 |
| [simulator/domain/__init__.py](/simulator/domain/__init__.py) | Python | 1 | 0 | 1 | 2 |
| [simulator/domain/events.py](/simulator/domain/events.py) | Python | 77 | 0 | 23 | 100 |
| [simulator/domain/execution_info.py](/simulator/domain/execution_info.py) | Python | 90 | 1 | 17 | 108 |
| [simulator/domain/message.py](/simulator/domain/message.py) | Python | 101 | 3 | 17 | 121 |
| [simulator/domain/network_premitives.py](/simulator/domain/network_premitives.py) | Python | 264 | 20 | 66 | 350 |
| [simulator/domain/sphere.py](/simulator/domain/sphere.py) | Python | 21 | 2 | 4 | 27 |
| [simulator/domain/topology.py](/simulator/domain/topology.py) | Python | 163 | 22 | 27 | 212 |
| [simulator/experiment.py](/simulator/experiment.py) | Python | 132 | 11 | 40 | 183 |
| [simulator/ez_lib/__init__.py](/simulator/ez_lib/__init__.py) | Python | 1 | 0 | 1 | 2 |
| [simulator/ez_lib/cen_ctrl_handler.py](/simulator/ez_lib/cen_ctrl_handler.py) | Python | 64 | 16 | 14 | 94 |
| [simulator/ez_lib/cen_scheduler.py](/simulator/ez_lib/cen_scheduler.py) | Python | 382 | 50 | 45 | 477 |
| [simulator/ez_lib/ez_ctrl_handler.py](/simulator/ez_lib/ez_ctrl_handler.py) | Python | 51 | 3 | 12 | 66 |
| [simulator/ez_lib/ez_flow_tool.py](/simulator/ez_lib/ez_flow_tool.py) | Python | 671 | 78 | 106 | 855 |
| [simulator/ez_lib/ez_ob.py](/simulator/ez_lib/ez_ob.py) | Python | 102 | 6 | 29 | 137 |
| [simulator/ez_lib/ez_scheduler.py](/simulator/ez_lib/ez_scheduler.py) | Python | 20 | 55 | 5 | 80 |
| [simulator/ez_lib/ez_switch_handler.py](/simulator/ez_lib/ez_switch_handler.py) | Python | 213 | 39 | 39 | 291 |
| [simulator/ez_lib/ez_topo.py](/simulator/ez_lib/ez_topo.py) | Python | 36 | 0 | 9 | 45 |
| [simulator/ez_lib/p2p_scheduler.py](/simulator/ez_lib/p2p_scheduler.py) | Python | 630 | 78 | 79 | 787 |
| [simulator/ez_tracer.py](/simulator/ez_tracer.py) | Python | 344 | 37 | 60 | 441 |
| [simulator/flow_change_gen.py](/simulator/flow_change_gen.py) | Python | 48 | 0 | 7 | 55 |
| [simulator/flow_gen/__init__.py](/simulator/flow_gen/__init__.py) | Python | 1 | 0 | 1 | 2 |
| [simulator/flow_gen/flow_change_generator.py](/simulator/flow_gen/flow_change_generator.py) | Python | 422 | 21 | 68 | 511 |
| [simulator/flow_gen/k_shortest_paths.py](/simulator/flow_gen/k_shortest_paths.py) | Python | 100 | 3 | 28 | 131 |
| [simulator/flow_gen/link_failure_change_generator.py](/simulator/flow_gen/link_failure_change_generator.py) | Python | 122 | 0 | 20 | 142 |
| [simulator/flow_gen/mul_flow_change_generator.py](/simulator/flow_gen/mul_flow_change_generator.py) | Python | 394 | 79 | 75 | 548 |
| [simulator/flow_gen/path_generators.py](/simulator/flow_gen/path_generators.py) | Python | 357 | 19 | 44 | 420 |
| [simulator/flow_gen/random_change_generator.py](/simulator/flow_gen/random_change_generator.py) | Python | 16 | 33 | 2 | 51 |
| [simulator/misc/__init__.py](/simulator/misc/__init__.py) | Python | 1 | 0 | 1 | 2 |
| [simulator/misc/constants.py](/simulator/misc/constants.py) | Python | 85 | 16 | 30 | 131 |
| [simulator/misc/global_vars.py](/simulator/misc/global_vars.py) | Python | 10 | 0 | 1 | 11 |
| [simulator/misc/logger.py](/simulator/misc/logger.py) | Python | 60 | 32 | 15 | 107 |
| [simulator/misc/message_utils.py](/simulator/misc/message_utils.py) | Python | 8 | 0 | 3 | 11 |
| [simulator/misc/utils.py](/simulator/misc/utils.py) | Python | 70 | 0 | 24 | 94 |
| [src/central_ctrl.py](/src/central_ctrl.py) | Python | 241 | 89 | 68 | 398 |
| [src/global_ctrl.py](/src/global_ctrl.py) | Python | 298 | 43 | 53 | 394 |
| [src/local_ctrl.py](/src/local_ctrl.py) | Python | 433 | 205 | 150 | 788 |
| [src/muc/local_muc.py](/src/muc/local_muc.py) | Python | 129 | 1 | 21 | 151 |
| [src/muc/server_muc.py](/src/muc/server_muc.py) | Python | 102 | 1 | 28 | 131 |
| [src/muc/topo.py](/src/muc/topo.py) | Python | 46 | 3 | 14 | 63 |
| [src/topo.py](/src/topo.py) | Python | 73 | 18 | 23 | 114 |
| [src/topo/__init__.py](/src/topo/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [src/topo/b4.py](/src/topo/b4.py) | Python | 32 | 3 | 7 | 42 |
| [src/topo/basetopo.py](/src/topo/basetopo.py) | Python | 24 | 0 | 8 | 32 |
| [src/topo/example.py](/src/topo/example.py) | Python | 21 | 3 | 7 | 31 |
| [src/topo/get_random_topo.py](/src/topo/get_random_topo.py) | Python | 26 | 4 | 10 | 40 |
| [src/topo/internet2.py](/src/topo/internet2.py) | Python | 37 | 13 | 7 | 57 |
| [src/topo/rf_1239.py](/src/topo/rf_1239.py) | Python | 986 | 10 | 10 | 1,006 |
| [src/topo/rf_6462.py](/src/topo/rf_6462.py) | Python | 55 | 4 | 8 | 67 |
| [src/topo/topo_factory.py](/src/topo/topo_factory.py) | Python | 14 | 0 | 5 | 19 |
| [src/topo/triangle.py](/src/topo/triangle.py) | Python | 22 | 3 | 11 | 36 |
| [testbyxcj/__init__.py](/testbyxcj/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [testbyxcj/datasender.py](/testbyxcj/datasender.py) | Python | 88 | 8 | 16 | 112 |
| [testbyxcj/front/front.py](/testbyxcj/front/front.py) | Python | 84 | 6 | 15 | 105 |
| [testbyxcj/localwithid.py](/testbyxcj/localwithid.py) | Python | 57 | 16 | 19 | 92 |
| [testbyxcj/mix/S4.py](/testbyxcj/mix/S4.py) | Python | 42 | 13 | 19 | 74 |
| [testbyxcj/mix/__init__.py](/testbyxcj/mix/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [testbyxcj/mix/analys/draw_iperf.py](/testbyxcj/mix/analys/draw_iperf.py) | Python | 35 | 1 | 10 | 46 |
| [testbyxcj/mix/bricks/__init__.py](/testbyxcj/mix/bricks/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [testbyxcj/mix/bricks/basenet.py](/testbyxcj/mix/bricks/basenet.py) | Python | 13 | 0 | 3 | 16 |
| [testbyxcj/mix/bricks/basetopo.py](/testbyxcj/mix/bricks/basetopo.py) | Python | 24 | 0 | 8 | 32 |
| [testbyxcj/mix/bricks/flow_des.py](/testbyxcj/mix/bricks/flow_des.py) | Python | 32 | 2 | 10 | 44 |
| [testbyxcj/mix/bricks/message.py](/testbyxcj/mix/bricks/message.py) | Python | 21 | 1 | 4 | 26 |
| [testbyxcj/mix/consts.py](/testbyxcj/mix/consts.py) | Python | 29 | 7 | 5 | 41 |
| [testbyxcj/mix/data/draw_topo/draw_topo.py](/testbyxcj/mix/data/draw_topo/draw_topo.py) | Python | 62 | 10 | 16 | 88 |
| [testbyxcj/mix/global.py](/testbyxcj/mix/global.py) | Python | 648 | 86 | 79 | 813 |
| [testbyxcj/mix/local2.py](/testbyxcj/mix/local2.py) | Python | 447 | 34 | 68 | 549 |
| [testbyxcj/mix/localthread.py](/testbyxcj/mix/localthread.py) | Python | 649 | 58 | 92 | 799 |
| [testbyxcj/mix/logger.py](/testbyxcj/mix/logger.py) | Python | 60 | 4 | 15 | 79 |
| [testbyxcj/mix/multi_controller_topo.py](/testbyxcj/mix/multi_controller_topo.py) | Python | 177 | 32 | 27 | 236 |
| [testbyxcj/mix/scheduler/__init__.py](/testbyxcj/mix/scheduler/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [testbyxcj/mix/scheduler/main.py](/testbyxcj/mix/scheduler/main.py) | Python | 55 | 11 | 22 | 88 |
| [testbyxcj/mix/scheduler/scheduler.py](/testbyxcj/mix/scheduler/scheduler.py) | Python | 277 | 100 | 86 | 463 |
| [testbyxcj/mix/tools.py](/testbyxcj/mix/tools.py) | Python | 100 | 28 | 11 | 139 |
| [testbyxcj/mix/topo.py](/testbyxcj/mix/topo.py) | Python | 45 | 5 | 16 | 66 |
| [testbyxcj/mix/topo3.py](/testbyxcj/mix/topo3.py) | Python | 67 | 11 | 16 | 94 |
| [testbyxcj/mix/trashbin/buf.py](/testbyxcj/mix/trashbin/buf.py) | Python | 218 | 34 | 52 | 304 |
| [testbyxcj/mix/trashbin/buffer_manager.py](/testbyxcj/mix/trashbin/buffer_manager.py) | Python | 59 | 8 | 12 | 79 |
| [testbyxcj/mix/trashbin/deprecatedbm.py](/testbyxcj/mix/trashbin/deprecatedbm.py) | Python | 73 | 4 | 18 | 95 |
| [testbyxcj/mix/trashbin/fours_topo.py](/testbyxcj/mix/trashbin/fours_topo.py) | Python | 30 | 4 | 9 | 43 |
| [testbyxcj/testCtypes.py](/testbyxcj/testCtypes.py) | Python | 4 | 0 | 1 | 5 |
| [testbyxcj/testJason.py](/testbyxcj/testJason.py) | Python | 53 | 42 | 34 | 129 |
| [testbyxcj/testProcess.py](/testbyxcj/testProcess.py) | Python | 37 | 66 | 33 | 136 |
| [testbyxcj/testeventlet.py](/testbyxcj/testeventlet.py) | Python | 75 | 87 | 46 | 208 |
| [testbyxcj/testpickle.py](/testbyxcj/testpickle.py) | Python | 36 | 63 | 38 | 137 |
| [testbyxcj/testpk.py](/testbyxcj/testpk.py) | Python | 50 | 30 | 32 | 112 |

[summary](results.md)