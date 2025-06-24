      // check current axis saturation
      // when it is unsaturated
      // if (!prevReadings[i].xyz_flags[j].sat){
      //   // conditions for negative saturation and positive saturation 
      //   if ((filt_cur_axis_reading - prevReadings[i].data_arr[j]) < -thres)
      //   {
      //     prevReadings[i].xyz_flags[j].sat = true; prevReadings[i].xyz_flags[j].sat_dir = true; // change the flags
      //     prevReadings[i].sat_val[j] = abs(prevReadings[i].data_arr[j]); // collect the saturation bounds
      //     corrected_axis_reading = filt_cur_axis_reading+2*prevReadings[i].sat_val[j]-initReadings[i].data_arr[j];
      //   }
      //   else if ((filt_cur_axis_reading - prevReadings[i].data_arr[j]) > thres)
      //   {
      //     prevReadings[i].xyz_flags[j].sat = true; prevReadings[i].xyz_flags[j].sat_dir = false;
      //     prevReadings[i].sat_val[j] = abs(prevReadings[i].data_arr[j]); // collect the saturation bounds
      //     corrected_axis_reading = filt_cur_axis_reading-2*prevReadings[i].sat_val[j]-initReadings[i].data_arr[j];
      //   }
      //   else
      //   {
      //     corrected_axis_reading = filt_cur_axis_reading-initReadings[i].data_arr[j];
      //   }
      // }
      // else {
      //   // when in positive saturation
      //   if (prevReadings[i].xyz_flags[j].sat_dir)
      //   {
      //     // condition to return to unsaturation
      //     if ((filt_cur_axis_reading - prevReadings[i].data_arr[j]) > thres)
      //     {
      //       prevReadings[i].xyz_flags[j].sat = false;
      //       corrected_axis_reading = filt_cur_axis_reading-initReadings[i].data_arr[j];
      //     }
      //     else
      //     {
      //       corrected_axis_reading = filt_cur_axis_reading+2*prevReadings[i].sat_val[j]-initReadings[i].data_arr[j];
      //     }
      //   }
      //   // when in negative saturation
      //   else if (!prevReadings[i].xyz_flags[j].sat_dir)
      //   {
      //     // condition to return to unsaturation
      //     if ((filt_cur_axis_reading - prevReadings[i].data_arr[j]) < -thres)
      //     {
      //       prevReadings[i].xyz_flags[j].sat = false;
      //       corrected_axis_reading = filt_cur_axis_reading-initReadings[i].data_arr[j];
      //     }
      //     else
      //     {
      //       corrected_axis_reading = filt_cur_axis_reading-2*prevReadings[i].sat_val[j]-initReadings[i].data_arr[j];
      //     }
      //   }
      // }