# Technical short film

## GPU Silo final cut

`gpu_silo.mp4` runs 3:00.500 in 3840 × 2160 at 24 fps. The first frame shows the whole silo and its rural site. The 17-second introduction uses orbit frames 63 through 470, starting 2.625 seconds into the original camera move. The narrator reads the owner's four sentences over this wide shot. The six-line card fades in from 2.0 to 2.5 seconds. The full 22.50-second silent closing orbit opens on the Starlink antenna. [Intro script and closing copy](technical_review.json) · [Opening voice recording](../audio/gpu_silo_intro.flac)

| Starts | Sequence | Frames |
| --- | --- | ---: |
| 0:00.000 | Narrated wide view of the rural site | 408 |
| 0:17.000 | Construction, services and control room | 2,071 |
| 1:43.292 | Four IFC studies covering the shaft, pod, cooler and turbine deck | 576 |
| 2:07.292 | Vertical IFC thermal section and cooling ride-through | 737 |
| 2:38.000 | Silent rural orbit and project credit | 540 |

The thumbnail uses the uncropped clean orbit frame at 19.750 seconds, frame 474 with zero-based numbering. Only the letters in the sky change. The compact editorial graphics continue through the technical sequence. The opening figures refer to the 256-rack installed capacity, gross generation and the silo footprint. The operating-envelope cue gives the 46 MW computing ceiling.

## Original technical cut

The 4K edition follows the 4:22 construction cut at double speed. At 24 frames per second, 3,145 picture frames run for 2:11.042. The original has an odd number of frames. Sampling frames 0, 2, …, 6,288 retains both endpoints and adds half a delivery frame to the exact half-duration. The silo closes at 0:05. The original 23 chapter boundaries move to the first corresponding delivery frame.

## Picture and sound

The model supplies the construction stages and camera path. Blender EEVEE renders the daylight construction. Cycles supplies the control-room scene, the four IFC studies and the closing blue-hour orbit. The camera moves nearer the carrier and turbine components within their six-second studies. The trucks have individually modelled day cabs, wheel arches and suspension. The mixer carries a tapered drum, discharge chute and access ladder. The crane houses have stacked ballast, wraparound cab glazing and twin winches. The turbine close-up shows the compressor flanges, combustor, oil filters, coupling, alternator and cable tray. Equipment nameplates and the roof antenna’s lettering belong to the scene. Technical cards, equipment references and drawing labels enter in postproduction.

Kokoro v1.0 records each passage independently in the `am_eric` voice. Cue windows follow the shortened picture. Pronunciation text, display text, caption timing and published product references accompany the recordings. The release includes a narrated film with selectable English captions, a clean silent picture master, the separate voice recording, the animated short model and the four component excerpts.

## Assumptions for review

| Subject | Treatment in the film |
| --- | --- |
| Road traffic | The reference animation contains 189 representative truck journeys. The short shows 57 complete trips. The traffic pass reserves the swept tractor, trailer and cargo footprints at quarter source-frame intervals, with a margin for travel and articulation between samples. Compatible trips keep their load-transfer frames. Other deliveries appear as previously staged loads on trestles. Construction quantities and chapter times come from the project programme. |
| Cranes and access plant | Crawler shoe chains, rollers, sprockets, counterweights, cab fittings, hoist details and hydraulic lines are illustrative. The tracked access machine retains the animated boom and work-basket envelope. The 62 m booms come from the model. A commercial crawler’s maximum class rating depends on its configuration and working radius. |
| Shaft study | The stationary shaft, level-six bay-one twin trusses and root lock use mesh vertices and GlobalIds from the issued IFC. The hub uses the project drum and ring dimensions. One empty holder makes two 45° indexes with a dwell. The six-second study compresses the drive motion. |
| Turbine packages | The project assumes two propane units rated at 25 MW each and 94.5 t per set. Casing hardware, gauges, fuel lines, louvers and couplings illustrate an aeroderivative package. The 60 Hz LM2500 DLE commercial reference is rated at 22.7 MW net on natural gas at ISO conditions. Site performance, package footprint and propane rating require a vendor selection. |
| Computing | Each of the 256 physical positions has a project allowance of 195 kW. Four positions give 780 kW per pod. The 46 MW normal IT ceiling allows 235 full-power racks at 45.825 MW with 21 spare. Operators choose the mix within available power and cooling. |
| Cooling | Each cooler has a 2 MW design rating. At rating, 26 units provide 52 MW against 51.25 MW of design heat rejection. The thermal calculation uses 6,524 m³ of 25% propylene-glycol solution, a 10 K swing, maintained circulation and stratification for the modelled 76-minute ride-through. |
| Power and emergencies | Normal operation uses the turbines. The 4 MW auxiliary allowance leaves 46 MW for IT at nameplate output. Site conditions can lower available output. Four 2.5 MW emergency diesels support up to 7 MW of priority IT after essential services. |

The approved facility exchange has SHA-256 `891dac77a0a1de577bf8da9c6e3301cef85eed5dc9f379a6a4a01bbb74bb7764`. It provides the registration datum for all four IFC studies. The moving carrier is part of the film and its companion GLB. [Project design](report.md) · [Inputs](project.json) · [Timed script and references](technical_short.json)

## Equipment references

| System | Manufacturer reference |
| --- | --- |
| Road haulage | Kenworth lists the standard-hood T880 for heavy haul and offers T880 configurations for tankers and ready-mix bodies. The 14.6 m deck and 21.8 t payload are project trailer inputs. [Kenworth T880 brochure](https://www.kenworth.com/media/3oxf4lky/t880-brochure-01-29-2019.pdf) |
| Gas turbine | GE Vernova lists the LM2500 DLE at 22.7 MW net in 60 Hz simple-cycle ISO natural-gas service. The catalogue rating gives the audience a commercial comparison for the project’s assumed propane machines. [GE Vernova 60 Hz factsheet](https://www.gevernova.com/content/dam/gepower/global/en_US/documents/gas/gas-turbines/aero-products-specs/lm2500-60hz-fact-sheet-product-specifications.pdf) |
| Emergency generator | Cat offers 3516C 60 Hz configurations up to 2,500 ekW standby. [Cat 3516C](https://www.cat.com/en_US/products/new/power-systems/electric-power/diesel-generator-sets/1000028912.html) |
| GPU rack | The Vera Rubin NVL72 configuration has 72 Rubin GPUs and 36 Vera CPUs. Electrical provision comes from the project. [NVIDIA Vera Rubin NVL72](https://www.nvidia.com/en-gb/data-center/vera-rubin-nvl72/) |
| Liquid distribution | Vertiv lists 1,368 kW nominal capacity at 4 K approach for its XDU1350. This is a thermal-duty comparison. Pod packaging is project-specific. [Vertiv XDU1350 planning guide](https://www.vertiv.com/4908a3/globalassets/products/thermal-management/high-density-solutions/liebert-xdu-coolant-distribution-units/vertiv-liebert-xdu1350-coolant-distribution-unit-application-and-planning-guide-xdu1350b-sl-71309.pdf) |
| Dry cooler | Güntner lists a V-shape VARIO family capacity range reaching 2,000 kW. The project depicts a bespoke outward-discharge wall assembly. [Güntner V-shape VARIO](https://guntner.com/products/dry-coolers/v-shape-vario-dc-nla) |
| Crawler and work platform | The Liebherr LR 1300.1 SX is a 300 t class crawler. Palazzani lists 37 m working height for its XTJ 37+ tracked platform. [Liebherr LR 1300.1 SX](https://www.liebherr.com/en-int/p/lr1300-5387355) · [Palazzani XTJ series](https://www.palazzani.it/piattaforme-serie-xtj/) |

## Rebuild

Use Python 3.12 with the repository requirements, Blender 4.5 LTS, and FFmpeg with libass and libx264. The checked-in audio allows an offline rebuild. The work directory holds the scene bake and numbered photography frames. Use a fresh work directory after a geometry, timing or lighting edit. Reusing the same directory resumes an interrupted render from its existing frames.

```console
python -m gpu_silo technical-short --blender blender --work renders/technical-work --output renders/technical-short
```

To regenerate the recording, pass `--models` pointing at Kokoro’s `kokoro-v1.0.onnx` and `voices-v1.0.bin` with `kokoro-onnx` and `soundfile` installed. Regenerate the shaft excerpt from the issued file with `python -m gpu_silo.technical_shaft path/to/GPU_Silo.ifc`.

### Assemble the final cut

The commands below use the technical cut's native 4K construction frames in `frames`, its recording and timings in `technical`, the revised takes from `gpu_silo.review_voice` in `voice`, the graded rural orbit in `final_360.mp4` and the four-shot `IFC_vid_thermal.mp4`. Render the 78 control-room frames at full size using the revised facade from `gpu_silo.review_orbit_source`. Install Pillow and SoundFile for compositing and audio. Impact and Franklin Gothic Medium Condensed reproduce the selected display lettering.

```console
blender -b --python-exit-code 9 -P renderer/technical_blender.py -- bake office-4k 1993 2070 --facade review-inputs/facade.npz --percent 100 --samples 8
python -m gpu_silo.final_voice conform technical voice audio work
python -m gpu_silo.review_orbit_overlay final_360.mp4 orbit
python -m gpu_silo.review_thumbnails final_360.mp4 work/cover delivery --final-only
python -m gpu_silo.final_film body construction frames work
python -m gpu_silo.final_film body office office-4k work
python -m gpu_silo.final_film body studies frames work
python -m gpu_silo.final_film assemble orbit/final_360_overlay.mp4 IFC_vid_thermal.mp4 voice work delivery
python -m gpu_silo.validation.verify_final_film work delivery IFC_vid_thermal.mp4 orbit/final_360_overlay.mp4
```

The orbit compositor writes the full closing orbit and `wide_intro_picture.mp4` to the same directory. To reuse an approved closing master, run the compositor with `--intro-only`. The assembly also writes the standalone narrated `gpu_silo_intro.mp4`. The full film carries English captions and chapters. To change the opening, set its source frame interval (end exclusive) and voice pace in `design/technical_review.json`, then run `python -m gpu_silo.final_voice record models audio`. The recording step checks that all four sentences finish inside the picture cut.
